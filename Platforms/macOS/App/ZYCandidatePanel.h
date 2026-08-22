#import <AppKit/AppKit.h>
#include "ZYEngine.h"
@protocol ZYCandidatePanelDelegate <NSObject>
- (void)candidatePanelDidChooseIndex:(NSUInteger)index;
- (void)candidatePanelDidDeleteIndex:(NSUInteger)index;
- (void)candidatePanelToggleScript;
- (void)candidatePanelToggleHelp;
- (void)candidatePanelRequestClearLearning;
- (void)candidatePanelConfirmClearLearning;
@end
@interface ZYCandidatePanel : NSPanel
@property(nonatomic,readonly) NSUInteger columns;
@property(nonatomic,readonly) BOOL quickHelpVisible;
@property(nonatomic,readonly) BOOL clearLearningConfirmationVisible;
@property(nonatomic,weak) id<ZYCandidatePanelDelegate> candidateDelegate;
- (void)updateCandidates:(const ZYCandidate *)items deletable:(const BOOL *)deletable count:(NSUInteger)count selected:(NSUInteger)selected chinese:(BOOL)chinese simplified:(BOOL)simplified;
- (void)updateWords:(NSArray<NSString*> *)words count:(NSUInteger)count selected:(NSUInteger)selected chinese:(BOOL)chinese simplified:(BOOL)simplified modeLabel:(NSString *)modeLabel;
- (void)setPreeditText:(NSString *)text;
- (void)setDeleteMode:(BOOL)enabled;
- (void)showNearRect:(NSRect)rect;
- (void)toggleQuickHelp;
- (void)closeQuickHelp;
- (void)showClearLearningConfirmation;
- (void)closeClearLearningConfirmation;
- (void)showClearLearningResult:(BOOL)success;
@end
