#import "ZYInputController.h"
#import "ZYRuntime.h"
#import "ZYAccessibilityCaret.h"
#import <Carbon/Carbon.h>
#include <math.h>

#define ZY_MAX_PIECES 64
#define ZY_PIECE_TEXT 128
#define ZY_PIECE_QUERY 192
#define ZY_PIECE_PRON 384

static NSString *const ZYOutputSimplifiedKey=@"ZYOutputSimplified";

typedef enum { ZYPieceWord=1, ZYPiecePunctuation=2, ZYPieceLiteral=3 } ZYPieceKind;
typedef enum { ZYSpecialCandidateNone=0, ZYSpecialCandidateEmoji=1, ZYSpecialCandidatePunctuation=2 } ZYSpecialCandidateMode;

static NSArray<NSString*> *ZYSpecialCandidates(ZYSpecialCandidateMode mode){
    static NSArray<NSString*> *emoji=nil,*punctuation=nil;
    if(!emoji) emoji=@[@"😀",@"😃",@"😄",@"😁",@"😆",@"😅",@"😂",@"🤣",@"😊",@"😇",
        @"🙂",@"🙃",@"😉",@"😍",@"🥰",@"😘",@"😋",@"😜",@"🤪",@"🤔",
        @"🫡",@"🤗",@"🤭",@"🫢",@"🤫",@"🤐",@"😐",@"😑",@"😶",@"🙄",
        @"😏",@"😒",@"😔",@"😢",@"😭",@"😤",@"😡",@"🤬",@"😱",@"😨",
        @"😴",@"🤤",@"🤢",@"🤮",@"🤧",@"😷",@"🤒",@"🤕",@"🥳",@"😎",
        @"🤓",@"🧐",@"👍",@"👎",@"👌",@"🤌",@"✌️",@"🤞",@"🫶",@"🙏",
        @"👏",@"🙌",@"💪",@"❤️",@"🧡",@"💛",@"💚",@"💙",@"💜",@"🖤",
        @"🤍",@"💔",@"❣️",@"💕",@"💯",@"🔥",@"✨",@"⭐",@"🌟",@"🎉",
        @"🎊",@"✅",@"❌",@"⚠️",@"❓",@"❗",@"💡",@"📌",@"📍",@"🚀",
        @"🎁",@"🎂",@"☕",@"🍜",@"🍺",@"🍻"];
    if(!punctuation) punctuation=@[@"，",@"。",@"、",@"？",@"！",@"：",@"；",@"「",@"」",@"『",
        @"』",@"（",@"）",@"［",@"］",@"【",@"】",@"〔",@"〕",@"〈",
        @"〉",@"《",@"》",@"…",@"——",@"—",@"～",@"·",@"‧",@"／",
        @"＼",@"｜",@"＠",@"＃",@"＄",@"％",@"＆",@"＊",@"＋",@"－",
        @"＝",@"＿"];
    return mode==ZYSpecialCandidateEmoji?emoji:(mode==ZYSpecialCandidatePunctuation?punctuation:@[]);
}
static NSString *ZYSpecialModeLabel(ZYSpecialCandidateMode mode){return mode==ZYSpecialCandidateEmoji?@"Emoji":(mode==ZYSpecialCandidatePunctuation?@"標點":@"");}
static NSUInteger ZYSpecialPageSize(ZYSpecialCandidateMode mode){return mode==ZYSpecialCandidateNone?20:50;}
typedef struct {
    ZYPieceKind kind; uint32_t candidateID;
    char text[ZY_PIECE_TEXT]; char query[ZY_PIECE_QUERY]; char pron[ZY_PIECE_PRON];
} ZYPendingPiece;

static void ccopy(char *dst,size_t cap,const char *src){if(!cap)return;size_t n=src?strlen(src):0;if(n>=cap)n=cap-1;if(n)memcpy(dst,src,n);dst[n]=0;}
static void cappend(char *dst,size_t cap,const char *src,const char *separator){size_t n=strlen(dst),s=src?strlen(src):0,sep=(separator&&*dst&&*src)?strlen(separator):0;if(n+sep+s>=cap)return;if(sep){memcpy(dst+n,separator,sep);n+=sep;}if(s){memcpy(dst+n,src,s);n+=s;}dst[n]=0;}
static void flushLearningRun(char *word,size_t wordCap,char *query,size_t queryCap,char *pron,size_t pronCap,NSUInteger *pieceCount){
    if(*pieceCount>1&&word[0]&&query[0])ZYRuntimeLearnPhrase(word,query,pron);
    if(wordCap)word[0]=0;if(queryCap)query[0]=0;if(pronCap)pron[0]=0;*pieceCount=0;
}

@implementation ZYInputController {
    NSMutableString *_composition;
    ZYPendingPiece _pieces[ZY_MAX_PIECES]; NSUInteger _pieceCount;
    ZYCandidate _candidates[40]; NSUInteger _candidateCount,_selected,_pageStart;
    ZYCandidatePanel *_panel;
    NSUInteger _panelReleaseGeneration;
    BOOL _panelReleaseScheduled;
    NSRect _lastCaretRect;
    BOOL _chinese,_simplified,_shiftDown,_shiftAlone,_optionDown;
    ZYSpecialCandidateMode _specialMode;
}

- (instancetype)initWithServer:(IMKServer *)server delegate:(id)delegate client:(id)inputClient {
    self=[super initWithServer:server delegate:delegate client:inputClient];
    if(self){
        _composition=[NSMutableString string];
        _chinese=YES;
        NSUserDefaults *defaults=[NSUserDefaults standardUserDefaults];
        _simplified=[defaults boolForKey:ZYOutputSimplifiedKey];
    }
    return self;
}
- (ZYCandidatePanel *)ensureCandidatePanel {
    _panelReleaseGeneration++;
    _panelReleaseScheduled=NO;
    if(!_panel){_panel=[[ZYCandidatePanel alloc]init];_panel.candidateDelegate=self;}
    return _panel;
}
- (void)releaseCandidatePanel {
    _panelReleaseGeneration++;
    _panelReleaseScheduled=NO;
    if(!_panel)return;
    _panel.candidateDelegate=nil;
    [_panel orderOut:nil];
    [_panel close];
    _panel=nil;
}
- (void)hideCandidatePanel {
    if(!_panel)return;
    [_panel orderOut:nil];
    if(_panelReleaseScheduled)return;
    _panelReleaseScheduled=YES;
    NSUInteger generation=++_panelReleaseGeneration;
    __weak ZYInputController *weakSelf=self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(2.0*NSEC_PER_SEC)),dispatch_get_main_queue(),^{
        ZYInputController *strongSelf=weakSelf;
        if(!strongSelf||!strongSelf->_panelReleaseScheduled||generation!=strongSelf->_panelReleaseGeneration)return;
        if(strongSelf->_panel&&!strongSelf->_panel.isVisible)[strongSelf releaseCandidatePanel];
    });
}
- (void)inputControllerWillClose { [self releaseCandidatePanel]; ZYRuntimeMaybeFlush(); [super inputControllerWillClose]; }
- (void)deactivateServer:(id)sender { [self releaseCandidatePanel]; [super deactivateServer:sender]; }
- (NSUInteger)recognizedEvents:(id)sender { (void)sender; return NSEventMaskKeyDown|NSEventMaskFlagsChanged; }

- (NSString *)piecesText {
    NSMutableString *s=[NSMutableString string];
    for(NSUInteger i=0;i<_pieceCount;i++){NSString *p=[NSString stringWithUTF8String:_pieces[i].text];if(p)[s appendString:p];}
    return s;
}
- (NSString *)preeditText { NSMutableString *s=[[self piecesText] mutableCopy]; if(_composition.length)[s appendString:_composition]; return s; }
static BOOL ZYUsableCaretRect(NSRect rect) {
    return isfinite(rect.origin.x) && isfinite(rect.origin.y) &&
           isfinite(rect.size.width) && isfinite(rect.size.height) &&
           rect.size.width >= 0.0 && rect.size.height > 0.0 &&
           !(fabs(rect.origin.x)<0.5 && fabs(rect.origin.y)<0.5);
}
- (NSRect)clientRect:(id)client {
    @autoreleasepool {
        // IMKTextInput provides the primary candidate-window positioning API.
        // Query only the final inline character once.  Some clients return an
        // unusable rectangle; in that case move directly to the document-range
        // fallback instead of scanning backward through the whole preedit string.
        if([client respondsToSelector:@selector(attributesForCharacterIndex:lineHeightRectangle:)]) {
            id<IMKTextInput> textClient=(id<IMKTextInput>)client;
            NSInteger cursor=(NSInteger)[self preeditText].length;
            if(cursor>0) cursor--;
            if(cursor>=0) {
                NSRect lineRect=NSZeroRect;
                @try {
                    [textClient attributesForCharacterIndex:(NSUInteger)cursor lineHeightRectangle:&lineRect];
                } @catch(__unused NSException *e) {
                    lineRect=NSZeroRect;
                }
                if(ZYUsableCaretRect(lineRect)){
                    _lastCaretRect=lineRect;
                    return lineRect;
                }
            }
        }

        // Document-relative ranges are a compatibility fallback.  IMKTextInput
        // clients are allowed to report NSNotFound when document access is unavailable.
        if([client respondsToSelector:@selector(firstRectForCharacterRange:actualRange:)]) {
            @try {
                NSRange caret=NSMakeRange(NSNotFound,0);
                if([client respondsToSelector:@selector(markedRange)]) {
                    NSRange marked=[client markedRange];
                    if(marked.location!=NSNotFound) caret=NSMakeRange(NSMaxRange(marked),0);
                }
                if(caret.location==NSNotFound && [client respondsToSelector:@selector(selectedRange)]) {
                    NSRange selected=[client selectedRange];
                    if(selected.location!=NSNotFound) caret=NSMakeRange(NSMaxRange(selected),0);
                }
                if(caret.location!=NSNotFound) {
                    NSRect rect=[client firstRectForCharacterRange:caret actualRange:NULL];
                    if(ZYUsableCaretRect(rect)){_lastCaretRect=rect;return rect;}
                }
            } @catch(__unused NSException *e) {}
        }

        // AX is the final live-position fallback for unusual clients.
        NSRect ax=ZYAccessibilityCaretRect();
        if(ZYUsableCaretRect(ax)){_lastCaretRect=ax;return ax;}

        // Never substitute the mouse pointer for a text caret.  If a client briefly
        // fails to answer during an update, keep the most recent real caret instead.
        if(ZYUsableCaretRect(_lastCaretRect))return _lastCaretRect;
        NSScreen *screen=[NSScreen mainScreen];
        if(!screen) screen=[[NSScreen screens] firstObject];
        NSRect vis=screen?[screen visibleFrame]:NSMakeRect(0,0,1440,900);
        return NSMakeRect(NSMidX(vis),NSMidY(vis),1,20);
    }
}
- (void)updateMarked:(id)client {
    if(!_chinese)return;
    @autoreleasepool {
        NSString *s=[self preeditText];
        [client setMarkedText:s selectionRange:NSMakeRange(s.length,0) replacementRange:NSMakeRange(NSNotFound,NSNotFound)];
    }
}

- (void)refreshCandidates:(id)client {
    _specialMode=ZYSpecialCandidateNone;_candidateCount=0;_selected=0;_pageStart=0;

    if(_chinese&&_composition.length){
        _candidateCount=ZYRuntimeLookup(_composition.UTF8String,_candidates,40);
    }
    [self refreshPanel:client];
}
- (void)refreshPanel:(id)client {
    if(!_chinese||!_candidateCount){[self hideCandidatePanel];return;}
    ZYCandidatePanel *panel=[self ensureCandidatePanel];
    NSUInteger pageSize=ZYSpecialPageSize(_specialMode);_pageStart=(_selected/pageSize)*pageSize;NSUInteger count=MIN(pageSize,_candidateCount-_pageStart);
    if(_specialMode!=ZYSpecialCandidateNone){
        NSArray<NSString*> *all=ZYSpecialCandidates(_specialMode);
        NSArray<NSString*> *page=[all subarrayWithRange:NSMakeRange(_pageStart,count)];
        [panel updateWords:page count:count selected:_selected-_pageStart chinese:_chinese simplified:_simplified modeLabel:ZYSpecialModeLabel(_specialMode)];
    }else{
        BOOL deletable[50]={0};for(NSUInteger i=0;i<count;i++)deletable[i]=ZYRuntimeCandidateHasLearning(_candidates[_pageStart+i].id);
        [panel updateCandidates:_candidates+_pageStart deletable:deletable count:count selected:_selected-_pageStart chinese:_chinese simplified:_simplified];
    }
    [panel showNearRect:[self clientRect:client]];
}
- (void)openSpecialCandidates:(ZYSpecialCandidateMode)mode client:(id)client {
    NSArray<NSString*> *items=ZYSpecialCandidates(mode);if(!items.count)return;
    _specialMode=mode;_candidateCount=items.count;_selected=0;_pageStart=0;[self refreshPanel:client];
}
- (void)closeSpecialCandidates:(id)client {
    if(_specialMode==ZYSpecialCandidateNone)return;
    _specialMode=ZYSpecialCandidateNone;[self refreshCandidates:client];
}
- (void)showInternalState:(id)client { [self updateMarked:client]; [self refreshCandidates:client]; }

- (BOOL)appendPieceForCandidate:(ZYCandidate)c client:(id)client {
    if(c.segment_count){
        if(c.segment_count>ZY_CANDIDATE_MAX_SEGMENTS||_pieceCount+c.segment_count>ZY_MAX_PIECES){NSBeep();return NO;}
        NSUInteger total=0;for(uint8_t j=0;j<c.segment_count;j++)total+=c.segment_consume_codepoints[j];
        if(!total||total>_composition.length){NSBeep();return NO;}
        NSString *source=[_composition copy];NSUInteger qpos=0,startPiece=_pieceCount;
        for(uint8_t j=0;j<c.segment_count;j++){
            uint8_t consume=c.segment_consume_codepoints[j];uint32_t sid=c.segment_ids[j];
            if(!consume||qpos+consume>source.length){_pieceCount=startPiece;NSBeep();return NO;}
            char word[ZY_PIECE_TEXT]={0},pron[ZY_PIECE_PRON]={0};
            if(ZYRuntimeCandidateWord(sid,word,sizeof(word))!=0||ZYRuntimeCandidatePron(sid,pron,sizeof(pron))!=0){_pieceCount=startPiece;NSBeep();return NO;}
            NSString *q=[source substringWithRange:NSMakeRange(qpos,consume)];
            ZYPendingPiece *p=&_pieces[_pieceCount++];memset(p,0,sizeof(*p));p->candidateID=sid;p->kind=ZYPieceWord;ccopy(p->text,sizeof(p->text),word);ccopy(p->query,sizeof(p->query),q.UTF8String);ccopy(p->pron,sizeof(p->pron),pron);qpos+=consume;
        }
        NSString *remain=[source substringFromIndex:qpos];[_composition setString:remain];
        [self updateMarked:client];[self refreshCandidates:client];return YES;
    }
    if(_pieceCount>=ZY_MAX_PIECES){NSBeep();return NO;}
    NSUInteger consume=c.consume_codepoints?c.consume_codepoints:_composition.length;if(consume>_composition.length)consume=_composition.length;
    NSString *q=[_composition substringToIndex:consume];NSString *remain=[_composition substringFromIndex:consume];
    ZYPendingPiece *p=&_pieces[_pieceCount++];memset(p,0,sizeof(*p));p->candidateID=c.id;p->kind=c.literal?ZYPieceLiteral:ZYPieceWord;ccopy(p->text,sizeof(p->text),c.word);ccopy(p->query,sizeof(p->query),q.UTF8String);
    if(!c.literal)ZYRuntimeCandidatePron(c.id,p->pron,sizeof(p->pron));
    [_composition setString:remain];
    [self updateMarked:client];[self refreshCandidates:client];return YES;
}
- (BOOL)chooseAbsolute:(NSUInteger)idx client:(id)client {if(idx>=_candidateCount)return NO;return [self appendPieceForCandidate:_candidates[idx] client:client];}
- (BOOL)chooseSpecialAbsolute:(NSUInteger)idx client:(id)client {
    NSArray<NSString*> *items=ZYSpecialCandidates(_specialMode);if(_specialMode==ZYSpecialCandidateNone||idx>=items.count)return NO;
    NSString *item=items[idx];_specialMode=ZYSpecialCandidateNone;_candidateCount=0;_selected=0;_pageStart=0;
    [self appendPunctuation:item client:client];[self refreshCandidates:client];return YES;
}
- (BOOL)chooseCurrentAbsolute:(NSUInteger)idx client:(id)client {return _specialMode!=ZYSpecialCandidateNone?[self chooseSpecialAbsolute:idx client:client]:[self chooseAbsolute:idx client:client];}
- (BOOL)chooseSelected:(id)client {return [self chooseCurrentAbsolute:_selected client:client];}
- (BOOL)moveSelectionTo:(NSUInteger)index client:(id)client {
    if(index>=_candidateCount)return NO;
    _selected=index;
    [self refreshPanel:client];
    return YES;
}

- (void)appendPunctuation:(NSString *)punct client:(id)client {
    // A boundary resolves the current composition into staged candidates first.
    for(int guard=0;_composition.length&&guard<16;guard++){if(!_candidateCount)[self refreshCandidates:client];NSUInteger before=_composition.length;if(![self chooseSelected:client]||_composition.length>=before)break;}
    if(_composition.length)return;
    if(_pieceCount>=ZY_MAX_PIECES){NSBeep();return;}ZYPendingPiece *p=&_pieces[_pieceCount++];memset(p,0,sizeof(*p));p->kind=ZYPiecePunctuation;ccopy(p->text,sizeof(p->text),punct.UTF8String);[self updateMarked:client];
}

- (void)learnAndCommit:(id)client {
    if(!_pieceCount)return;
    ZYRuntimeBeginLearningEvent();
    char runWord[768]={0},runQuery[1024]={0},runPron[1536]={0};NSUInteger runPieces=0;
    for(NSUInteger i=0;i<_pieceCount;i++){
        ZYPendingPiece *p=&_pieces[i];
        if(p->kind!=ZYPieceWord){flushLearningRun(runWord,sizeof(runWord),runQuery,sizeof(runQuery),runPron,sizeof(runPron),&runPieces);continue;}
        if(p->candidateID<0x80000000u)ZYRuntimeLearnWord(p->candidateID,p->query);
        else if(p->candidateID!=UINT32_MAX)ZYRuntimeLearnPhrase(p->text,p->query,p->pron);
        cappend(runWord,sizeof(runWord),p->text,"");cappend(runQuery,sizeof(runQuery),p->query,"");cappend(runPron,sizeof(runPron),p->pron,"\x1f");runPieces++;
    }
    flushLearningRun(runWord,sizeof(runWord),runQuery,sizeof(runQuery),runPron,sizeof(runPron),&runPieces);
    NSString *text=[self piecesText];NSString *output=ZYRuntimeOutputString(text,_simplified);[client insertText:output replacementRange:NSMakeRange(NSNotFound,NSNotFound)];
    _pieceCount=0;[_composition setString:@""];_candidateCount=0;_selected=0;[self hideCandidatePanel];ZYRuntimeMaybeFlush();
}

- (void)toggleLanguage:(id)client {
    if(_chinese&&_composition.length&&_candidateCount)[self chooseSelected:client];
    if(_chinese&&_pieceCount)[self learnAndCommit:client];
    _chinese=!_chinese;_shiftAlone=NO;_specialMode=ZYSpecialCandidateNone;_candidateCount=0;
    if(_chinese){[self updateMarked:client];[self refreshCandidates:client];}
    else{[client setMarkedText:@"" selectionRange:NSMakeRange(0,0) replacementRange:NSMakeRange(NSNotFound,NSNotFound)];[self hideCandidatePanel];}
}
- (void)toggleScript:(id)client {_simplified=!_simplified;[[NSUserDefaults standardUserDefaults] setBool:_simplified forKey:ZYOutputSimplifiedKey];[self refreshPanel:client];}

static NSString *zhuyinForKeyCode(unsigned short k){switch(k){
    case 18:return @"ㄅ";case 19:return @"ㄉ";case 20:return @"ˇ";case 21:return @"ˋ";case 23:return @"ㄓ";case 22:return @"ˊ";case 26:return @"˙";case 28:return @"ㄚ";case 25:return @"ㄞ";case 29:return @"ㄢ";case 27:return @"ㄦ";
    case 12:return @"ㄆ";case 13:return @"ㄊ";case 14:return @"ㄍ";case 15:return @"ㄐ";case 17:return @"ㄔ";case 16:return @"ㄗ";case 32:return @"ㄧ";case 34:return @"ㄛ";case 31:return @"ㄟ";case 35:return @"ㄣ";
    case 0:return @"ㄇ";case 1:return @"ㄋ";case 2:return @"ㄎ";case 3:return @"ㄑ";case 5:return @"ㄕ";case 4:return @"ㄘ";case 38:return @"ㄨ";case 40:return @"ㄜ";case 37:return @"ㄠ";case 41:return @"ㄤ";
    case 6:return @"ㄈ";case 7:return @"ㄌ";case 8:return @"ㄏ";case 9:return @"ㄒ";case 11:return @"ㄖ";case 45:return @"ㄙ";case 46:return @"ㄩ";case 43:return @"ㄝ";case 47:return @"ㄡ";case 44:return @"ㄥ";default:return nil;}}
static NSInteger shiftSlot(unsigned short k){switch(k){case 18:return 0;case 19:return 1;case 20:return 2;case 21:return 3;case 23:return 4;case 22:return 5;case 26:return 6;case 28:return 7;case 25:return 8;case 29:return 9;case 0:return 10;case 11:return 11;case 8:return 12;case 2:return 13;case 14:return 14;case 3:return 15;case 5:return 16;case 4:return 17;case 34:return 18;case 38:return 19;default:return -1;}}
static BOOL isASCIIEnglishLetter(NSString *text){if(text.length!=1)return NO;unichar c=[text characterAtIndex:0];return (c>='A'&&c<='Z')||(c>='a'&&c<='z');}
static BOOL ZYIsToneCharacter(unichar c){return c==0x02C9||c==0x02CA||c==0x02C7||c==0x02CB||c==0x02D9;}
static BOOL ZYCompositionNeedsFirstTone(NSString *composition){
    if(!composition.length)return NO;unichar last=[composition characterAtIndex:composition.length-1];
    if(ZYIsToneCharacter(last))return NO;
    return last>=0x3105&&last<=0x3129;
}
static NSString *chinesePunctuation(unsigned short k,BOOL shift){if(!shift){if(k==33)return @"「";if(k==30)return @"」";return nil;}switch(k){case 43:return @"，";case 47:return @"。";case 44:return @"？";case 18:return @"！";case 41:return @"：";case 39:return @"；";case 42:return @"、";case 25:return @"（";case 29:return @"）";case 33:return @"「";case 30:return @"」";case 50:return @"『";case 24:return @"』";case 28:return @"…";case 27:return @"—";default:return nil;}}

- (BOOL)handleEvent:(NSEvent *)event client:(id)client {
    if(event.type==NSEventTypeFlagsChanged&&(event.keyCode==58||event.keyCode==61)){
        BOOL down=(event.modifierFlags&NSEventModifierFlagOption)!=0;
        if(_optionDown!=down){_optionDown=down;[_panel setDeleteMode:down];}
        return YES;
    }
    if(event.type==NSEventTypeFlagsChanged&&(event.keyCode==56||event.keyCode==60)){
        BOOL down=(event.modifierFlags&NSEventModifierFlagShift)!=0;
        if(down&&!_shiftDown){_shiftDown=YES;_shiftAlone=YES;return YES;}
        if(!down&&_shiftDown){_shiftDown=NO;if(_shiftAlone){[self toggleLanguage:client];return YES;}return YES;}
    }
    if(event.type!=NSEventTypeKeyDown)return NO;
    NSEventModifierFlags systemModifiers=NSEventModifierFlagCommand|NSEventModifierFlagOption|NSEventModifierFlagControl;
    if(event.modifierFlags&systemModifiers)return NO;
    BOOL shift=(event.modifierFlags&NSEventModifierFlagShift)!=0;if(shift)_shiftAlone=NO;
    switch(event.keyCode){case kVK_F9:[self toggleScript:client];return YES;default:break;}
    if(!_chinese)return NO;
    if(!shift){
        switch(event.keyCode){
            case kVK_ANSI_Grave:[self openSpecialCandidates:ZYSpecialCandidateEmoji client:client];return YES;
            case kVK_ANSI_Quote:[self openSpecialCandidates:ZYSpecialCandidatePunctuation client:client];return YES;
            default:break;
        }
    }

    if(_candidateCount&&shift){NSInteger slot=shiftSlot(event.keyCode);if(slot>=0){NSUInteger idx=_pageStart+(NSUInteger)slot;if(idx<_candidateCount)[self chooseCurrentAbsolute:idx client:client];return YES;}}
    NSString *punct=chinesePunctuation(event.keyCode,shift);if(punct){if(_specialMode!=ZYSpecialCandidateNone)_specialMode=ZYSpecialCandidateNone;[self appendPunctuation:punct client:client];return YES;}
    if(shift&&isASCIIEnglishLetter(event.characters)){
        BOOL hadCandidates=_candidateCount!=0;
        if(_specialMode!=ZYSpecialCandidateNone)[self closeSpecialCandidates:client];
        if(_composition.length&&_candidateCount)[self chooseSelected:client];
        if(_pieceCount)[self learnAndCommit:client];
        NSString *latin=event.characters;
        if(!hadCandidates){
            NSString *base=[latin lowercaseString];
            BOOL caps=(event.modifierFlags&NSEventModifierFlagCapsLock)!=0;
            latin=caps?[base uppercaseString]:base;
        }
        [client insertText:latin replacementRange:NSMakeRange(NSNotFound,NSNotFound)];return YES;
    }
    NSUInteger pageSize=ZYSpecialPageSize(_specialMode);
    NSUInteger columns=_specialMode==ZYSpecialCandidateNone?(_panel?MAX((NSUInteger)1,_panel.columns):(NSUInteger)10):(NSUInteger)10;
    switch(event.keyCode){
        case 123: return _candidateCount?[self moveSelectionTo:_selected>0?_selected-1:0 client:client]:NO;
        case 124: return _candidateCount?[self moveSelectionTo:MIN(_candidateCount-1,_selected+1) client:client]:NO;
        case 126: return _candidateCount?[self moveSelectionTo:_selected>=columns?_selected-columns:_selected client:client]:NO;
        case 125: return _candidateCount?[self moveSelectionTo:MIN(_candidateCount-1,_selected+columns) client:client]:NO;
        case 116: return _candidateCount?[self moveSelectionTo:_selected>=pageSize?_selected-pageSize:0 client:client]:NO;
        case 121: return _candidateCount?[self moveSelectionTo:MIN(_candidateCount-1,_selected+pageSize) client:client]:NO;
        case 115: return _candidateCount?[self moveSelectionTo:0 client:client]:NO;
        case 119: return _candidateCount?[self moveSelectionTo:_candidateCount-1 client:client]:NO;
        case 51:
            if(_specialMode!=ZYSpecialCandidateNone){[self closeSpecialCandidates:client];return YES;}
            if(_composition.length){[_composition deleteCharactersInRange:NSMakeRange(_composition.length-1,1)];[self showInternalState:client];return YES;}
            if(_pieceCount){ZYPendingPiece p=_pieces[--_pieceCount];if(p.kind==ZYPieceWord||p.kind==ZYPieceLiteral)[_composition setString:[NSString stringWithUTF8String:p.query]?:@""];[self showInternalState:client];return YES;}return NO;
        case 53:
            if(_panel.clearLearningConfirmationVisible){[_panel closeClearLearningConfirmation];return YES;}
            if(_panel.quickHelpVisible){[_panel closeQuickHelp];return YES;}
            if(_specialMode!=ZYSpecialCandidateNone){[self closeSpecialCandidates:client];return YES;}
            if(_composition.length){[_composition setString:@""];_candidateCount=0;[self updateMarked:client];[self hideCandidatePanel];return YES;}
            if(_pieceCount){_pieceCount=0;[self updateMarked:client];return YES;}return NO;
        case 49:
            if(_specialMode!=ZYSpecialCandidateNone)return [self chooseSelected:client];
            if(_composition.length){
                if(ZYCompositionNeedsFirstTone(_composition)){[_composition appendString:@"ˉ"];[self updateMarked:client];[self refreshCandidates:client];return YES;}
                if(_candidateCount)return [self chooseSelected:client];
                return YES;
            }
            if(!_pieceCount&&_candidateCount==0){[client insertText:@" " replacementRange:NSMakeRange(NSNotFound,NSNotFound)];return YES;}
            [self appendPunctuation:@" " client:client];return YES;
        case 36:
            if(_specialMode!=ZYSpecialCandidateNone)return [self chooseSelected:client];
            if(_composition.length){if(_candidateCount)[self chooseSelected:client];return YES;}
            if(_pieceCount){[self learnAndCommit:client];return YES;}return NO;
        default: break;
    }
    NSString *z=zhuyinForKeyCode(event.keyCode);if(z){if(_specialMode!=ZYSpecialCandidateNone)_specialMode=ZYSpecialCandidateNone;[_composition appendString:z];[self updateMarked:client];[self refreshCandidates:client];return YES;}
    return NO;
}

- (void)candidatePanelDidChooseIndex:(NSUInteger)index {
    id client=[self client];NSUInteger absolute=_pageStart+index;
    [self chooseCurrentAbsolute:absolute client:client];
}
- (void)candidatePanelDidDeleteIndex:(NSUInteger)index {
    NSUInteger absolute=_pageStart+index;if(absolute>=_candidateCount)return;
    ZYCandidate c=_candidates[absolute];
    if(!ZYRuntimeRemoveCandidateLearning(c.id,_composition.UTF8String)){NSBeep();return;}
    [self refreshCandidates:[self client]];
}
- (void)candidatePanelToggleLanguage {}
- (void)candidatePanelToggleScript { [self toggleScript:[self client]]; }
- (void)candidatePanelToggleHelp { [_panel toggleQuickHelp]; }
- (void)candidatePanelRequestClearLearning {
    [_panel closeQuickHelp];
    [_panel showClearLearningConfirmation];
}
- (void)candidatePanelConfirmClearLearning {
    BOOL ok=ZYRuntimeClearLearning();
    if(ok&&_composition.length)[self refreshCandidates:[self client]];
    [_panel showClearLearningResult:ok];
}

- (NSMenu *)menu {
    NSMenu *m=[[NSMenu alloc]initWithTitle:@"逐音輸入法"];
    NSMenuItem *lang=[[NSMenuItem alloc]initWithTitle:_chinese?@"切換英文輸入":@"切換中文輸入" action:@selector(menuToggleLanguage:) keyEquivalent:@""];lang.target=self;[m addItem:lang];
    NSMenuItem *script=[[NSMenuItem alloc]initWithTitle:_simplified?@"改為繁體輸出":@"改為簡體輸出" action:@selector(menuToggleScript:) keyEquivalent:@""];script.target=self;[m addItem:script];return m;
}
- (void)menuToggleLanguage:(id)sender {(void)sender;[self toggleLanguage:[self client]];}
- (void)menuToggleScript:(id)sender {(void)sender;[self toggleScript:[self client]];}
@end
