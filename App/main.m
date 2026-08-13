// v0.1.5 -> v0.1.6: 將 IMKServer 改為 static 全域強引用，防止 ARC 釋放連線實體導致 macOS 點擊切換輸入法無響應
#import <Cocoa/Cocoa.h>
#import <InputMethodKit/InputMethodKit.h>
#import "ZYRuntime.h"

static IMKServer *gServer = nil;

@interface ZYAppDelegate : NSObject <NSApplicationDelegate>@end
@implementation ZYAppDelegate
- (void)applicationWillTerminate:(NSNotification *)n{(void)n;ZYRuntimeShutdown();}
@end

int main(int argc,const char *argv[]){
    (void)argc;(void)argv;
    @autoreleasepool {
        if(!ZYRuntimeInitialize()) return 2;
        NSApplication *app = [NSApplication sharedApplication];
        ZYAppDelegate *delegate = [ZYAppDelegate new];
        app.delegate = delegate;
        NSBundle *bundle = [NSBundle mainBundle];
        NSString *name = [bundle objectForInfoDictionaryKey:@"InputMethodConnectionName"];
        NSString *bid = bundle.bundleIdentifier;
        gServer = [[IMKServer alloc] initWithName:name bundleIdentifier:bid];
        [app run];
        ZYRuntimeShutdown();
        return 0;
    }
}
