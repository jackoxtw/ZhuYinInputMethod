#import "ZYCandidatePanel.h"
#import <dispatch/dispatch.h>
#include <math.h>
#include <string.h>

@interface ZYHelpPanel : NSPanel
@end
@implementation ZYHelpPanel
- (BOOL)canBecomeKeyWindow{return YES;}
- (BOOL)canBecomeMainWindow{return NO;}
@end

@class ZYCandidatePanel;
@interface ZYHelpView : NSView
@property(nonatomic,weak) ZYCandidatePanel *owner;
@end

@implementation ZYHelpView
- (BOOL)isFlipped{return YES;}
- (BOOL)acceptsFirstMouse:(NSEvent *)event{(void)event;return YES;}
- (BOOL)needsPanelToBecomeKey{return NO;}
- (BOOL)acceptsFirstResponder{return NO;}
- (BOOL)mouseDownCanMoveWindow{return NO;}
- (NSRect)helpCloseRect{return NSMakeRect(397,14,25,25);}
- (NSRect)helpBottomCloseRect{return NSMakeRect(306,412,108,34);}
- (NSRect)githubRect{return NSMakeRect(24,394,270,16);}
- (void)drawPill:(NSString *)text rect:(NSRect)rect{
    [[NSColor colorWithWhite:.22 alpha:1] setFill];
    [[NSBezierPath bezierPathWithRoundedRect:rect xRadius:6 yRadius:6] fill];
    NSDictionary *attrs=@{NSFontAttributeName:[NSFont monospacedSystemFontOfSize:11.5 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:[NSColor colorWithWhite:.96 alpha:1]};
    NSSize size=[text sizeWithAttributes:attrs];
    [text drawAtPoint:NSMakePoint(NSMidX(rect)-size.width/2,NSMidY(rect)-size.height/2) withAttributes:attrs];
}
- (void)drawShortcut:(NSString *)key detail:(NSString *)detail y:(CGFloat)y{
    [self drawPill:key rect:NSMakeRect(24,y,120,25)];
    NSDictionary *detailAttrs=@{NSFontAttributeName:[NSFont systemFontOfSize:12.5 weight:NSFontWeightRegular],NSForegroundColorAttributeName:[NSColor colorWithWhite:.90 alpha:1]};
    [detail drawAtPoint:NSMakePoint(158,y+4) withAttributes:detailAttrs];
}
- (void)drawRect:(NSRect)dirty{
    [super drawRect:dirty];
    [[NSColor colorWithWhite:.10 alpha:.985] setFill];
    [[NSBezierPath bezierPathWithRoundedRect:self.bounds xRadius:12 yRadius:12] fill];

    NSDictionary *title=@{NSFontAttributeName:[NSFont systemFontOfSize:16 weight:NSFontWeightBold],NSForegroundColorAttributeName:[NSColor colorWithRed:.62 green:.80 blue:1 alpha:1]};
    NSDictionary *subtitle=@{NSFontAttributeName:[NSFont systemFontOfSize:12.5],NSForegroundColorAttributeName:[NSColor colorWithWhite:.78 alpha:1]};
    [@"逐音輸入法" drawAtPoint:NSMakePoint(24,18) withAttributes:title];
    [@"快速使用說明" drawAtPoint:NSMakePoint(24,43) withAttributes:subtitle];

    NSRect close=self.helpCloseRect;
    [[NSColor colorWithWhite:.20 alpha:1] setFill];
    [[NSBezierPath bezierPathWithRoundedRect:close xRadius:7 yRadius:7] fill];
    NSDictionary *closeAttrs=@{NSFontAttributeName:[NSFont systemFontOfSize:15 weight:NSFontWeightMedium],NSForegroundColorAttributeName:[NSColor colorWithWhite:.82 alpha:1]};
    NSString *closeText=@"×";NSSize closeSize=[closeText sizeWithAttributes:closeAttrs];
    [closeText drawAtPoint:NSMakePoint(NSMidX(close)-closeSize.width/2,NSMidY(close)-closeSize.height/2-1) withAttributes:closeAttrs];

    [[NSColor colorWithWhite:.23 alpha:1] setStroke];
    NSBezierPath *divider=[NSBezierPath bezierPath];[divider moveToPoint:NSMakePoint(24,68)];[divider lineToPoint:NSMakePoint(416,68)];[divider stroke];

    NSDictionary *body=@{NSFontAttributeName:[NSFont systemFontOfSize:12.5 weight:NSFontWeightMedium],NSForegroundColorAttributeName:[NSColor colorWithWhite:.92 alpha:1]};
    [@"可連續輸入注音，不需要每個詞都先按 Enter。" drawAtPoint:NSMakePoint(24,82) withAttributes:body];
    NSDictionary *tones=@{NSFontAttributeName:[NSFont systemFontOfSize:12 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:[NSColor colorWithWhite:.72 alpha:1]};
    [@"五聲　ˉ ˊ ˇ ˋ ˙" drawAtPoint:NSMakePoint(24,104) withAttributes:tones];

    [self drawShortcut:@"Space" detail:@"閒置輸出空格；注音時第一聲 ˉ／確認候選" y:132];
    [self drawShortcut:@"Enter" detail:@"確認候選" y:162];
    [self drawShortcut:@"↑ ↓ ← →" detail:@"移動候選" y:192];
    [self drawShortcut:@"PgUp / PgDn" detail:@"切換候選頁" y:222];
    [self drawShortcut:@"Shift 1–0 / A–J" detail:@"有候選：快速選候選" y:252];
    [self drawShortcut:@"Shift + A–Z" detail:@"先送出中文，再輸入英文" y:282];
    [self drawShortcut:@"Option + 點選" detail:@"已學習候選顯示「刪除」後點選移除" y:312];
    [self drawShortcut:@"F9" detail:@"切換繁體／簡體輸出" y:342];
    [self drawShortcut:@"`  /  '" detail:@"Emoji ／ 中文標點" y:372];

    NSDictionary *githubAttrs=@{NSFontAttributeName:[NSFont monospacedSystemFontOfSize:10.5 weight:NSFontWeightMedium],NSForegroundColorAttributeName:[NSColor colorWithRed:.56 green:.74 blue:1 alpha:1],NSUnderlineStyleAttributeName:@(NSUnderlineStyleSingle)};
    [@"GitHub：github.com/jackoxtw/ZhuYinInputMethod" drawAtPoint:NSMakePoint(NSMinX(self.githubRect),NSMinY(self.githubRect)+3) withAttributes:githubAttrs];

    NSRect bottom=self.helpBottomCloseRect;
    NSDictionary *versionAttrs=@{NSFontAttributeName:[NSFont monospacedSystemFontOfSize:11 weight:NSFontWeightMedium],NSForegroundColorAttributeName:[NSColor colorWithWhite:.55 alpha:1]};
    [@"v0.1.50" drawAtPoint:NSMakePoint(24,NSMidY(bottom)-6) withAttributes:versionAttrs];
    [[NSColor colorWithWhite:.25 alpha:1] setFill];
    [[NSBezierPath bezierPathWithRoundedRect:bottom xRadius:8 yRadius:8] fill];
    NSDictionary *buttonAttrs=@{NSFontAttributeName:[NSFont systemFontOfSize:13 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:NSColor.whiteColor};
    NSString *button=@"關閉";NSSize bs=[button sizeWithAttributes:buttonAttrs];
    [button drawAtPoint:NSMakePoint(NSMidX(bottom)-bs.width/2,NSMidY(bottom)-bs.height/2) withAttributes:buttonAttrs];
}
- (void)mouseDown:(NSEvent *)event{
    NSPoint p=[self convertPoint:event.locationInWindow fromView:nil];
    if(NSPointInRect(p,self.githubRect)){[[NSWorkspace sharedWorkspace] openURL:[NSURL URLWithString:@"https://github.com/jackoxtw/ZhuYinInputMethod"]];return;}
    if(NSPointInRect(p,self.helpCloseRect)||NSPointInRect(p,self.helpBottomCloseRect)){
        [self.owner closeQuickHelp];return;
    }
}
@end

@interface ZYCandidatePanel (ZYClearLearningInternal)
- (void)candidateViewConfirmClearLearning;
@end

@interface ZYClearLearningPanel : NSPanel
@end
@implementation ZYClearLearningPanel
- (BOOL)canBecomeKeyWindow{return YES;}
- (BOOL)canBecomeMainWindow{return NO;}
@end

typedef NS_ENUM(NSUInteger, ZYClearLearningViewState){
    ZYClearLearningViewStateConfirm=0,
    ZYClearLearningViewStateSuccess=1,
    ZYClearLearningViewStateFailure=2,
};

@interface ZYClearLearningView : NSView
@property(nonatomic,weak) ZYCandidatePanel *owner;
@property(nonatomic) ZYClearLearningViewState state;
@end

@implementation ZYClearLearningView
- (BOOL)isFlipped{return YES;}
- (BOOL)acceptsFirstMouse:(NSEvent *)event{(void)event;return YES;}
- (BOOL)needsPanelToBecomeKey{return NO;}
- (BOOL)acceptsFirstResponder{return NO;}
- (BOOL)mouseDownCanMoveWindow{return NO;}
- (NSRect)cancelRect{return NSMakeRect(52,138,130,34);}
- (NSRect)confirmRect{return NSMakeRect(202,138,186,34);}
- (NSRect)closeRect{return NSMakeRect(145,138,150,34);}
- (void)drawButton:(NSString *)title rect:(NSRect)rect danger:(BOOL)danger{
    NSColor *fill=danger?[NSColor colorWithRed:.56 green:.17 blue:.17 alpha:1]:[NSColor colorWithWhite:.25 alpha:1];
    [fill setFill];[[NSBezierPath bezierPathWithRoundedRect:rect xRadius:8 yRadius:8] fill];
    NSDictionary *attrs=@{NSFontAttributeName:[NSFont systemFontOfSize:13 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:NSColor.whiteColor};
    NSSize size=[title sizeWithAttributes:attrs];[title drawAtPoint:NSMakePoint(NSMidX(rect)-size.width/2,NSMidY(rect)-size.height/2) withAttributes:attrs];
}
- (void)drawRect:(NSRect)dirty{
    [super drawRect:dirty];
    [[NSColor colorWithWhite:.10 alpha:.985] setFill];[[NSBezierPath bezierPathWithRoundedRect:self.bounds xRadius:12 yRadius:12] fill];
    if(self.state==ZYClearLearningViewStateConfirm){
        NSDictionary *title=@{NSFontAttributeName:[NSFont systemFontOfSize:16 weight:NSFontWeightBold],NSForegroundColorAttributeName:[NSColor colorWithRed:1 green:.82 blue:.45 alpha:1]};
        [@"⚠ 確定要清除學習資料嗎？" drawAtPoint:NSMakePoint(24,20) withAttributes:title];
        NSMutableParagraphStyle *ps=[[NSMutableParagraphStyle alloc]init];ps.lineBreakMode=NSLineBreakByWordWrapping;
        NSDictionary *body=@{NSFontAttributeName:[NSFont systemFontOfSize:12.5],NSForegroundColorAttributeName:[NSColor colorWithWhite:.90 alpha:1],NSParagraphStyleAttributeName:ps};
        NSString *text=@"將清除最近使用、常用詞頻、選字偏好、Query Preferred 與自訂學習詞組。\n內建詞庫、台灣詞庫、繁簡、Emoji 與其他設定不受影響。此操作無法復原。";
        [text drawWithRect:NSMakeRect(24,52,392,72) options:NSStringDrawingUsesLineFragmentOrigin|NSStringDrawingUsesFontLeading attributes:body];
        [self drawButton:@"取消" rect:self.cancelRect danger:NO];
        [self drawButton:@"清除學習資料" rect:self.confirmRect danger:YES];
    }else{
        BOOL ok=self.state==ZYClearLearningViewStateSuccess;
        NSString *titleText=ok?@"✓ 學習資料已清除":@"無法清除學習資料";
        NSString *bodyText=ok?@"新的選字與詞頻學習會從現在重新開始。":@"學習資料未完成清除，請稍後再試。";
        NSDictionary *title=@{NSFontAttributeName:[NSFont systemFontOfSize:17 weight:NSFontWeightBold],NSForegroundColorAttributeName:ok?[NSColor colorWithRed:.55 green:.90 blue:.62 alpha:1]:[NSColor colorWithRed:1 green:.55 blue:.55 alpha:1]};
        NSDictionary *body=@{NSFontAttributeName:[NSFont systemFontOfSize:13],NSForegroundColorAttributeName:[NSColor colorWithWhite:.90 alpha:1]};
        NSSize ts=[titleText sizeWithAttributes:title];[titleText drawAtPoint:NSMakePoint(NSMidX(self.bounds)-ts.width/2,44) withAttributes:title];
        NSSize bs=[bodyText sizeWithAttributes:body];[bodyText drawAtPoint:NSMakePoint(NSMidX(self.bounds)-bs.width/2,84) withAttributes:body];
        if(!ok)[self drawButton:@"關閉" rect:self.closeRect danger:NO];
    }
}
- (void)mouseDown:(NSEvent *)event{
    NSPoint p=[self convertPoint:event.locationInWindow fromView:nil];
    if(self.state==ZYClearLearningViewStateConfirm){
        if(NSPointInRect(p,self.cancelRect)){[self.owner closeClearLearningConfirmation];return;}
        if(NSPointInRect(p,self.confirmRect)){[self.owner candidateViewConfirmClearLearning];return;}
    }else if(self.state==ZYClearLearningViewStateFailure&&NSPointInRect(p,self.closeRect)){
        [self.owner closeClearLearningConfirmation];return;
    }
}
@end

@interface ZYCandidatePanel ()
- (void)candidateViewDidChooseIndex:(NSUInteger)index;
- (void)candidateViewDidDeleteIndex:(NSUInteger)index;
- (void)candidateViewToggleScript;
- (void)candidateViewToggleHelp;
- (void)candidateViewRequestClearLearning;
- (void)candidateViewConfirmClearLearning;
@end

@interface ZYCandidateView : NSView {
@private
    CGFloat _textFontSizes[50];
    CGFloat _textVerticalOffsets[50];
}
@property(nonatomic,weak) ZYCandidatePanel *panel;
@property(nonatomic) NSUInteger count,selected,rows,columns;
@property(nonatomic) CGFloat rowHeight;
@property(nonatomic) BOOL chinese,simplified;
@property(nonatomic) BOOL deleteMode;
@property(nonatomic,strong) NSArray<NSString*> *words;
@property(nonatomic,strong) NSArray<NSNumber*> *deletable;
@property(nonatomic,copy) NSString *modeLabel;
- (void)prepareCandidateTextLayout;
@end

static NSParagraphStyle *ZYSharedCandidateParagraphStyle(void){
    static NSParagraphStyle *style=nil;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        NSMutableParagraphStyle *paragraph=[[NSMutableParagraphStyle alloc]init];
        paragraph.alignment=NSTextAlignmentCenter;
        paragraph.lineBreakMode=NSLineBreakByCharWrapping;
        paragraph.lineSpacing=0;
        style=[paragraph copy];
    });
    return style;
}

static NSDictionary *ZYShortcutLabelAttributes(void){
    static NSDictionary *attrs=nil;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        attrs=@{NSFontAttributeName:[NSFont systemFontOfSize:9 weight:NSFontWeightBold],
                NSForegroundColorAttributeName:[NSColor colorWithWhite:.65 alpha:1]};
    });
    return attrs;
}

static NSArray<NSString*> *ZYCandidateShortcuts(void){
    static NSArray<NSString*> *shortcuts=nil;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shortcuts=@[@"1",@"2",@"3",@"4",@"5",@"6",@"7",@"8",@"9",@"0",
                    @"A",@"B",@"C",@"D",@"E",@"F",@"G",@"H",@"I",@"J"];
    });
    return shortcuts;
}

static NSDictionary *ZYCandidateTextAttributes(CGFloat fontSize){
    static NSDictionary *attrs[7]={nil,nil,nil,nil,nil,nil,nil};
    NSInteger size=(NSInteger)llround(fontSize);
    size=MAX((NSInteger)12,MIN((NSInteger)18,size));
    NSInteger index=size-12;
    // The normal input path uses one candidate font size at a time.  Creating
    // every system font from 12 through 18 on the first completed syllable can
    // eagerly start expensive FontServices/graphics caches.  Keep the same
    // immutable attributes, but instantiate only the actually used size.
    if(!attrs[index]){
        attrs[index]=@{NSFontAttributeName:[NSFont systemFontOfSize:(CGFloat)size weight:NSFontWeightMedium],
                      NSForegroundColorAttributeName:NSColor.whiteColor,
                      NSParagraphStyleAttributeName:ZYSharedCandidateParagraphStyle()};
    }
    return attrs[index];
}

static NSDictionary *ZYModeLabelAttributes(void){
    static NSDictionary *attrs=nil;static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{ attrs=@{NSFontAttributeName:[NSFont systemFontOfSize:9 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:[NSColor colorWithWhite:.72 alpha:1]}; });
    return attrs;
}
static NSDictionary *ZYScriptShortcutAttributes(BOOL simplified){
    static NSDictionary *normal=nil,*simple=nil;static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        normal=@{NSFontAttributeName:[NSFont systemFontOfSize:7.5 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:[NSColor colorWithWhite:.35 alpha:.85]};
        simple=@{NSFontAttributeName:[NSFont systemFontOfSize:7.5 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:[NSColor colorWithWhite:1 alpha:.72]};
    });
    return simplified?simple:normal;
}
static NSDictionary *ZYScriptLabelAttributes(BOOL simplified){
    static NSDictionary *normal=nil,*simple=nil;static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        normal=@{NSFontAttributeName:[NSFont systemFontOfSize:15 weight:NSFontWeightBold],NSForegroundColorAttributeName:[NSColor colorWithRed:.14 green:.20 blue:.29 alpha:1]};
        simple=@{NSFontAttributeName:[NSFont systemFontOfSize:15 weight:NSFontWeightBold],NSForegroundColorAttributeName:NSColor.whiteColor};
    });
    return simplified?simple:normal;
}
static NSDictionary *ZYHelpLabelAttributes(void){
    static NSDictionary *attrs=nil;static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{ attrs=@{NSFontAttributeName:[NSFont systemFontOfSize:10 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:[NSColor colorWithWhite:.88 alpha:1]}; });
    return attrs;
}
static NSDictionary *ZYClearLearningLabelAttributes(void){
    static NSDictionary *attrs=nil;static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{ attrs=@{NSFontAttributeName:[NSFont systemFontOfSize:9 weight:NSFontWeightSemibold],NSForegroundColorAttributeName:[NSColor colorWithRed:1 green:.78 blue:.78 alpha:1]}; });
    return attrs;
}

@implementation ZYCandidateView
- (BOOL)isFlipped{return YES;}
- (BOOL)acceptsFirstMouse:(NSEvent *)event{(void)event;return YES;}
- (BOOL)needsPanelToBecomeKey{return NO;}
- (BOOL)acceptsFirstResponder{return NO;}
- (BOOL)mouseDownCanMoveWindow{return NO;}
- (NSRect)scriptRect{return NSMakeRect(732,6,48,32);}
- (NSRect)helpRect{return NSMakeRect(732,42,48,18);}
- (NSRect)clearLearningRect{return NSMakeRect(732,MAX(86.0,NSHeight(self.bounds)-24.0),48,18);}

- (void)prepareCandidateTextLayout{
    memset(_textFontSizes,0,sizeof(_textFontSizes));
    memset(_textVerticalOffsets,0,sizeof(_textVerticalOffsets));
    if(!self.count||!self.columns)return;
    @autoreleasepool {
        CGFloat cellW=720.0/self.columns,cellH=self.rowHeight,y0=6;
        for(NSUInteger i=0;i<self.count&&i<50&&i<self.words.count;i++){
            NSUInteger row=i/self.columns,col=i%self.columns;
            NSRect r=NSMakeRect(6+col*cellW,y0+row*cellH,cellW-4,cellH-4);
            NSRect textRect=NSInsetRect(r,self.columns>=10?4:8,self.columns>=10?4:6);
            if(self.columns<10)textRect.origin.y+=2;
            NSString *w=self.words[i];
            CGFloat fontSize=self.columns>=10?(w.length>3?13.0:18.0):(self.columns==5?16.0:15.0);
            // Candidate preparation is on the per-key hot path.  Do not ask
            // NSStringDrawing/CoreText to measure every candidate: all normal
            // candidate cells are single-line.  Four-column long words use a
            // conservative character-width estimate and retain the existing
            // 12pt lower bound; drawRect clips any remaining overflow.
            if(self.columns==4&&w.length*(NSUInteger)fontSize>(NSUInteger)NSWidth(textRect))fontSize=12.0;
            NSFont *font=ZYCandidateTextAttributes(fontSize)[NSFontAttributeName];
            CGFloat neededHeight=ceil(font.ascender-font.descender+font.leading);
            _textFontSizes[i]=fontSize;
            _textVerticalOffsets[i]=MAX(0.0,(NSHeight(textRect)-neededHeight)/2.0);
        }
    }
}

- (void)drawRect:(NSRect)dirty{
    [super drawRect:dirty];
    [[NSColor colorWithWhite:0.10 alpha:0.96] setFill];
    [[NSBezierPath bezierPathWithRoundedRect:self.bounds xRadius:10 yRadius:10] fill];

    NSArray<NSString*> *shortcuts=ZYCandidateShortcuts();
    CGFloat cellW=720.0/self.columns,cellH=self.rowHeight,y0=6;
    NSDictionary *shortcutLabelAttrs=ZYShortcutLabelAttributes();
    NSParagraphStyle *candidateParagraph=ZYSharedCandidateParagraphStyle();
    for(NSUInteger i=0;i<self.count&&i<50;i++){
        NSUInteger row=i/self.columns,col=i%self.columns;
        NSRect r=NSMakeRect(6+col*cellW,y0+row*cellH,cellW-4,cellH-4);
        BOOL sel=i==self.selected;
        NSColor *fillColor=sel?[NSColor colorWithRed:.20 green:.43 blue:.82 alpha:1]:[NSColor colorWithWhite:.18 alpha:1];
        [fillColor setFill];
        [[NSBezierPath bezierPathWithRoundedRect:r xRadius:6 yRadius:6] fill];

        if(i<shortcuts.count){
            NSString *lab=shortcuts[i];
            [lab drawAtPoint:NSMakePoint(NSMinX(r)+5,NSMinY(r)+3) withAttributes:shortcutLabelAttrs];
        }
        if(self.deleteMode&&i<self.deletable.count&&self.deletable[i].boolValue){
            [@"刪除" drawAtPoint:NSMakePoint(NSMaxX(r)-24,NSMinY(r)+3) withAttributes:ZYClearLearningLabelAttributes()];
        }

        NSString *w=self.words[i];
        NSRect textRect=NSInsetRect(r,self.columns>=10?4:8,self.columns>=10?4:6);
        if(self.columns<10) textRect.origin.y+=2;
        CGFloat fontSize=_textFontSizes[i]>0.0?_textFontSizes[i]:(self.columns>=10?(w.length>3?13.0:18.0):(self.columns==5?16.0:15.0));
        NSDictionary *attrs=ZYCandidateTextAttributes(fontSize);
        CGFloat dy=_textVerticalOffsets[i];
        textRect.origin.y+=dy;
        textRect.size.height-=dy;
        [NSGraphicsContext saveGraphicsState];
        NSRectClip(r);
        if(self.columns==4){
            [w drawWithRect:textRect
                    options:NSStringDrawingUsesLineFragmentOrigin|NSStringDrawingUsesFontLeading
                 attributes:attrs];
        }else{
            NSFont *font=attrs[NSFontAttributeName];
            CGFloat baseline=NSMinY(textRect)+(NSHeight(textRect)-(font.ascender-font.descender))/2.0-font.descender;
            NSPoint textOrigin=NSMakePoint(NSMidX(textRect)-w.length*fontSize/2.0,baseline);
            [w drawAtPoint:textOrigin withAttributes:attrs];
        }
        [NSGraphicsContext restoreGraphicsState];
    }

    if(self.modeLabel.length){
        NSDictionary *modeAttrs=ZYModeLabelAttributes();
        NSSize modeSize=[self.modeLabel sizeWithAttributes:modeAttrs];
        [self.modeLabel drawAtPoint:NSMakePoint(756-modeSize.width/2,66) withAttributes:modeAttrs];
    }

    NSRect scriptRect=self.scriptRect;
    NSColor *scriptFill=self.simplified?[NSColor colorWithRed:.19 green:.37 blue:.73 alpha:1]:[NSColor colorWithWhite:.93 alpha:1];
    [scriptFill setFill];
    [[NSBezierPath bezierPathWithRoundedRect:scriptRect xRadius:10 yRadius:10] fill];
    NSDictionary *shortcutAttrs=ZYScriptShortcutAttributes(self.simplified);
    [@"F9" drawAtPoint:NSMakePoint(NSMinX(scriptRect)+4,NSMinY(scriptRect)+2) withAttributes:shortcutAttrs];
    NSString *scriptLabel=self.simplified?@"簡":@"繁";
    NSDictionary *scriptAttrs=ZYScriptLabelAttributes(self.simplified);
    NSSize scriptSize=[scriptLabel sizeWithAttributes:scriptAttrs];
    [scriptLabel drawAtPoint:NSMakePoint(NSMidX(scriptRect)-scriptSize.width/2,NSMidY(scriptRect)-scriptSize.height/2+1) withAttributes:scriptAttrs];

    NSRect helpRect=self.helpRect;
    [[NSColor colorWithWhite:.24 alpha:1] setFill];
    [[NSBezierPath bezierPathWithRoundedRect:helpRect xRadius:6 yRadius:6] fill];
    NSDictionary *helpAttrs=ZYHelpLabelAttributes();
    NSString *helpLabel=@"說明";NSSize helpSize=[helpLabel sizeWithAttributes:helpAttrs];
    [helpLabel drawAtPoint:NSMakePoint(NSMidX(helpRect)-helpSize.width/2,NSMidY(helpRect)-helpSize.height/2) withAttributes:helpAttrs];

    NSRect clearLearningRect=self.clearLearningRect;
    CGFloat clearLearningGap=NSMinY(clearLearningRect)-NSMaxY(helpRect);
    if(clearLearningGap>=18.0){
        CGFloat clearLearningSeparator=NSMinY(clearLearningRect)-9.0;
        [[NSColor colorWithWhite:.25 alpha:.75] setStroke];
        NSBezierPath *separator=[NSBezierPath bezierPath];
        [separator moveToPoint:NSMakePoint(734,clearLearningSeparator)];
        [separator lineToPoint:NSMakePoint(778,clearLearningSeparator)];
        [separator stroke];
    }
    [[NSColor colorWithRed:.34 green:.16 blue:.16 alpha:1] setFill];
    [[NSBezierPath bezierPathWithRoundedRect:clearLearningRect xRadius:6 yRadius:6] fill];
    NSDictionary *clearAttrs=ZYClearLearningLabelAttributes();
    NSString *clearLabel=@"清除學習";NSSize clearSize=[clearLabel sizeWithAttributes:clearAttrs];
    [clearLabel drawAtPoint:NSMakePoint(NSMidX(clearLearningRect)-clearSize.width/2,NSMidY(clearLearningRect)-clearSize.height/2) withAttributes:clearAttrs];
}

- (void)mouseDown:(NSEvent *)event{
    NSPoint p=[self convertPoint:event.locationInWindow fromView:nil];
    if(NSPointInRect(p,self.scriptRect)){[self.panel candidateViewToggleScript];return;}
    if(NSPointInRect(p,self.helpRect)){[self.panel candidateViewToggleHelp];return;}
    if(NSPointInRect(p,self.clearLearningRect)){[self.panel candidateViewRequestClearLearning];return;}
    CGFloat cellW=720.0/self.columns;
    if(p.x<6||p.x>=726||p.y<6||p.y>=6+self.rowHeight*self.rows)return;
    NSUInteger row=(NSUInteger)((p.y-6)/self.rowHeight),col=(NSUInteger)((p.x-6)/cellW),idx=row*self.columns+col;
    if(row<self.rows&&col<self.columns&&idx<self.count){if(self.deleteMode&&idx<self.deletable.count&&self.deletable[idx].boolValue)[self.panel candidateViewDidDeleteIndex:idx];else [self.panel candidateViewDidChooseIndex:idx];}
}
@end

@implementation ZYCandidatePanel{ZYCandidateView *_cv;ZYHelpPanel *_helpPanel;ZYHelpView *_helpView;ZYClearLearningPanel *_clearLearningPanel;ZYClearLearningView *_clearLearningView;NSUInteger _clearLearningResultToken;}
- (BOOL)canBecomeKeyWindow{return YES;}
- (BOOL)canBecomeMainWindow{return NO;}
- (instancetype)init{
    self=[super initWithContentRect:NSMakeRect(0,0,786,110)
                         styleMask:NSWindowStyleMaskBorderless|NSWindowStyleMaskNonactivatingPanel
                           backing:NSBackingStoreBuffered defer:NO];
    if(self){
        self.level=NSStatusWindowLevel;self.opaque=NO;self.backgroundColor=NSColor.clearColor;self.hasShadow=YES;self.hidesOnDeactivate=NO;self.ignoresMouseEvents=NO;self.becomesKeyOnlyIfNeeded=YES;
        self.collectionBehavior=NSWindowCollectionBehaviorCanJoinAllSpaces|NSWindowCollectionBehaviorFullScreenAuxiliary;
        _cv=[[ZYCandidateView alloc]initWithFrame:self.contentView.bounds];_cv.autoresizingMask=NSViewWidthSizable|NSViewHeightSizable;
        _cv.columns=10;_cv.rows=2;_cv.rowHeight=38;_cv.panel=self;
        self.contentView=_cv;
    }
    return self;
}
- (NSUInteger)columns{return _cv.columns?:10;}
- (void)setDeleteMode:(BOOL)enabled { if(_cv.deleteMode==enabled)return;_cv.deleteMode=enabled;[_cv setNeedsDisplay:YES]; }
- (void)candidateViewDidChooseIndex:(NSUInteger)index {
    [self.candidateDelegate candidatePanelDidChooseIndex:index];
}
- (void)candidateViewDidDeleteIndex:(NSUInteger)index { [self.candidateDelegate candidatePanelDidDeleteIndex:index]; }
- (void)candidateViewToggleScript {
    [self.candidateDelegate candidatePanelToggleScript];
}
- (void)candidateViewToggleHelp {
    [self.candidateDelegate candidatePanelToggleHelp];
}
- (void)candidateViewRequestClearLearning {
    [self.candidateDelegate candidatePanelRequestClearLearning];
}
- (void)candidateViewConfirmClearLearning {
    [self.candidateDelegate candidatePanelConfirmClearLearning];
}
- (void)resizeForRows:(NSUInteger)rows{
    CGFloat desiredHeight=MAX(110.0,12.0+_cv.rowHeight*rows);
    NSSize current=self.contentView.bounds.size;
    CGFloat height=self.isVisible?MAX(current.height,desiredHeight):desiredHeight;
    NSSize target=NSMakeSize(786,height);
    if(!NSEqualSizes(current,target))[self setContentSize:target];
    NSRect bounds=self.contentView.bounds;
    if(!NSEqualRects(_cv.frame,bounds))_cv.frame=bounds;
}

- (void)updateWords:(NSArray<NSString*> *)words count:(NSUInteger)count selected:(NSUInteger)selected chinese:(BOOL)chinese simplified:(BOOL)simplified modeLabel:(NSString *)modeLabel{
    _cv.chinese=chinese;_cv.simplified=simplified;_cv.words=words?:@[];
    count=MIN(count,(NSUInteger)50);count=MIN(count,(NSUInteger)_cv.words.count);
    _cv.count=count;_cv.selected=selected;_cv.modeLabel=modeLabel?:@"";
    _cv.columns=10;_cv.rowHeight=38;
    NSUInteger rows=MIN((NSUInteger)5,MAX((NSUInteger)1,(count+9)/10));
    _cv.rows=rows;[self resizeForRows:rows];[_cv prepareCandidateTextLayout];[_cv setNeedsDisplay:YES];
}

- (void)updateCandidates:(const ZYCandidate*)items deletable:(const BOOL *)deletable count:(NSUInteger)count selected:(NSUInteger)selected chinese:(BOOL)chinese simplified:(BOOL)simplified{
    NSMutableArray<NSString*> *a=[NSMutableArray arrayWithCapacity:MIN(count,20)];NSMutableArray<NSNumber*> *flags=[NSMutableArray arrayWithCapacity:MIN(count,20)];
    NSUInteger maxChars=0;
    for(NSUInteger i=0;i<count&&i<20;i++){
        NSString *s=[NSString stringWithUTF8String:items[i].word]?:@"";
        [a addObject:s];
        [flags addObject:@(deletable&&deletable[i])];
        maxChars=MAX(maxChars,s.length);
    }
    NSUInteger columns=maxChars<=2?10:(maxChars<=5?5:4);
    _cv.chinese=chinese;_cv.simplified=simplified;_cv.words=a;_cv.deletable=flags;_cv.count=a.count;_cv.selected=selected;_cv.modeLabel=@"";
    _cv.columns=columns;
    _cv.rowHeight=columns==10?38:(columns==5?48:58);
    NSUInteger rows=MAX((NSUInteger)1,(a.count+columns-1)/columns);
    _cv.rows=rows;[self resizeForRows:rows];[_cv prepareCandidateTextLayout];[_cv setNeedsDisplay:YES];
}

- (BOOL)clearLearningConfirmationVisible{return _clearLearningPanel&&_clearLearningPanel.isVisible;}
- (void)ensureClearLearningPanel {
    if(_clearLearningPanel)return;
    _clearLearningPanel=[[ZYClearLearningPanel alloc] initWithContentRect:NSMakeRect(0,0,440,190)
                                                          styleMask:NSWindowStyleMaskBorderless|NSWindowStyleMaskNonactivatingPanel
                                                            backing:NSBackingStoreBuffered defer:NO];
    _clearLearningPanel.level=NSStatusWindowLevel+1;_clearLearningPanel.opaque=NO;_clearLearningPanel.backgroundColor=NSColor.clearColor;_clearLearningPanel.hasShadow=YES;_clearLearningPanel.hidesOnDeactivate=NO;_clearLearningPanel.ignoresMouseEvents=NO;_clearLearningPanel.becomesKeyOnlyIfNeeded=YES;
    _clearLearningPanel.collectionBehavior=NSWindowCollectionBehaviorCanJoinAllSpaces|NSWindowCollectionBehaviorFullScreenAuxiliary;
    _clearLearningView=[[ZYClearLearningView alloc]initWithFrame:_clearLearningPanel.contentView.bounds];_clearLearningView.autoresizingMask=NSViewWidthSizable|NSViewHeightSizable;_clearLearningView.owner=self;_clearLearningView.state=ZYClearLearningViewStateConfirm;
    _clearLearningPanel.contentView=_clearLearningView;
}
- (void)positionClearLearningConfirmation {
    if(!_clearLearningPanel||!_clearLearningPanel.isVisible)return;
    NSScreen *screen=self.screen?:NSScreen.mainScreen;NSRect vis=screen.visibleFrame;NSRect f=self.frame;NSSize cs=_clearLearningPanel.frame.size;
    CGFloat gap=8.0,x=NSMaxX(f)+gap,y=NSMaxY(f)-cs.height;
    if(x+cs.width>NSMaxX(vis)-6.0)x=MAX(NSMinX(vis)+6.0,NSMinX(f)-gap-cs.width);
    if(y+cs.height>NSMaxY(vis)-6.0)y=NSMaxY(vis)-cs.height-6.0;
    if(y<NSMinY(vis)+6.0)y=NSMinY(vis)+6.0;
    [_clearLearningPanel setFrameOrigin:NSMakePoint(x,y)];
}
- (void)showClearLearningConfirmation {
    [self closeQuickHelp];[self ensureClearLearningPanel];_clearLearningResultToken++;
    _clearLearningView.state=ZYClearLearningViewStateConfirm;[_clearLearningView setNeedsDisplay:YES];
    [_clearLearningPanel orderFrontRegardless];[self positionClearLearningConfirmation];
}
- (void)closeClearLearningConfirmation {
    _clearLearningResultToken++;
    if(!_clearLearningPanel)return;
    _clearLearningView.owner=nil;
    [_clearLearningPanel orderOut:nil];
    [_clearLearningPanel close];
    _clearLearningPanel.contentView=nil;
    _clearLearningView=nil;
    _clearLearningPanel=nil;
}
- (void)showClearLearningResult:(BOOL)success {
    [self ensureClearLearningPanel];_clearLearningView.state=success?ZYClearLearningViewStateSuccess:ZYClearLearningViewStateFailure;[_clearLearningView setNeedsDisplay:YES];
    [_clearLearningPanel orderFrontRegardless];[self positionClearLearningConfirmation];
    if(success){NSUInteger token=++_clearLearningResultToken;__weak ZYCandidatePanel *weakSelf=self;dispatch_after(dispatch_time(DISPATCH_TIME_NOW,(int64_t)(1.2*NSEC_PER_SEC)),dispatch_get_main_queue(),^{ZYCandidatePanel *strongSelf=weakSelf;if(strongSelf&&token==strongSelf->_clearLearningResultToken)[strongSelf closeClearLearningConfirmation];});}
}
- (BOOL)quickHelpVisible{return _helpPanel&&_helpPanel.isVisible;}
- (void)positionQuickHelp {
    if(!_helpPanel||!_helpPanel.isVisible)return;
    NSScreen *screen=self.screen?:NSScreen.mainScreen;NSRect vis=screen.visibleFrame;NSRect f=self.frame;NSSize hs=_helpPanel.frame.size;
    CGFloat gap=6.0,x=NSMaxX(f)+gap,y=NSMaxY(f)-hs.height;
    if(x+hs.width>NSMaxX(vis)-6.0)x=MAX(NSMinX(vis)+6.0,NSMinX(f)-gap-hs.width);
    if(y+hs.height>NSMaxY(vis)-6.0)y=NSMaxY(vis)-hs.height-6.0;
    if(y<NSMinY(vis)+6.0)y=NSMinY(vis)+6.0;
    [_helpPanel setFrameOrigin:NSMakePoint(x,y)];
}
- (void)toggleQuickHelp {
    if(self.clearLearningConfirmationVisible)[self closeClearLearningConfirmation];
    if(_helpPanel&&_helpPanel.isVisible){[self closeQuickHelp];return;}
    if(!_helpPanel){
        _helpPanel=[[ZYHelpPanel alloc] initWithContentRect:NSMakeRect(0,0,440,460)
                                                 styleMask:NSWindowStyleMaskBorderless|NSWindowStyleMaskNonactivatingPanel
                                                   backing:NSBackingStoreBuffered defer:NO];
        _helpPanel.level=NSStatusWindowLevel+1;_helpPanel.opaque=NO;_helpPanel.backgroundColor=NSColor.clearColor;_helpPanel.hasShadow=YES;_helpPanel.hidesOnDeactivate=NO;_helpPanel.ignoresMouseEvents=NO;_helpPanel.becomesKeyOnlyIfNeeded=YES;
        _helpPanel.collectionBehavior=NSWindowCollectionBehaviorCanJoinAllSpaces|NSWindowCollectionBehaviorFullScreenAuxiliary;
        _helpView=[[ZYHelpView alloc]initWithFrame:_helpPanel.contentView.bounds];_helpView.autoresizingMask=NSViewWidthSizable|NSViewHeightSizable;_helpView.owner=self;
        _helpPanel.contentView=_helpView;
    }
    [_helpPanel orderFrontRegardless];[self positionQuickHelp];
}
- (void)closeQuickHelp{
    if(!_helpPanel)return;
    _helpView.owner=nil;
    [_helpPanel orderOut:nil];
    [_helpPanel close];
    _helpPanel.contentView=nil;
    _helpView=nil;
    _helpPanel=nil;
}
- (void)orderOut:(id)sender{
    [self closeQuickHelp];[self closeClearLearningConfirmation];
    _cv.words=@[];_cv.modeLabel=@"";_cv.count=0;_cv.selected=0;
    _cv.columns=10;_cv.rowHeight=38;_cv.rows=2;[_cv prepareCandidateTextLayout];
    [super orderOut:sender];
}

- (void)showNearRect:(NSRect)rect {
    NSScreen *screen=NSScreen.mainScreen;
    NSPoint anchor=NSMakePoint(NSMinX(rect),NSMidY(rect));
    for(NSScreen *s in NSScreen.screens){if(NSPointInRect(anchor,s.frame)){screen=s;break;}}
    NSRect vis=screen.visibleFrame;
    NSSize preferred=NSMakeSize(786,NSHeight(self.frame));
    NSSize size=NSMakeSize(MIN(preferred.width,NSWidth(vis)-12.0),MIN(preferred.height,NSHeight(vis)-12.0));
    if(size.width<1.0||size.height<1.0){[self orderOut:nil];return;}
    const CGFloat gap=6.0;
    CGFloat x=NSMaxX(rect)+gap;
    if(x+size.width>NSMaxX(vis)-6.0)x=NSMaxX(vis)-size.width-6.0;
    if(x<NSMinX(vis)+6.0)x=NSMinX(vis)+6.0;
    BOOL placeBelow=(NSMinY(rect)-gap-size.height)>=NSMinY(vis)+6.0;
    CGFloat y=placeBelow?NSMinY(rect)-gap-size.height:NSMaxY(rect)+gap;
    if(y+size.height>NSMaxY(vis)-6.0)y=NSMaxY(vis)-size.height-6.0;
    if(y<NSMinY(vis)+6.0)y=NSMinY(vis)+6.0;
    NSRect targetFrame=NSMakeRect(x,y,size.width,size.height);
    if(!NSEqualRects(self.frame,targetFrame))[self setFrame:targetFrame display:NO];
    if(!self.isVisible)[self orderFront:nil];
    [self positionQuickHelp];
    [self positionClearLearningConfirmation];
}
@end
