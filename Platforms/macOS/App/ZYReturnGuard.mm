#import "ZYReturnGuard.h"
#import <ApplicationServices/ApplicationServices.h>
#import <dispatch/dispatch.h>
#import <unistd.h>
#include <atomic>

NSString *const ZYStrictReturnGuardKey=@"ZYStrictReturnGuard";

typedef NS_ENUM(NSInteger, ZYReturnGuardRoute){
    ZYReturnGuardRouteNone=0,
    ZYReturnGuardRoutePerPID=1,
    ZYReturnGuardRouteAnnotatedSession=2,
    ZYReturnGuardRouteSession=3,
};

// Lifecycle objects are owned by the main thread. The tap callback itself runs on
// ZYReturnGuardThread's dedicated CFRunLoop, never on the InputMethodKit main loop.
static CFMachPortRef ZYReturnGuardTap=NULL;
static CFRunLoopSourceRef ZYReturnGuardSource=NULL;
static CFRunLoopRef ZYReturnGuardRunLoop=NULL;
static NSThread *ZYReturnGuardThread=nil;
static ZYReturnGuardHandler ZYReturnGuardHandlerBlock=nil;
static NSString *ZYReturnGuardLastFailure=nil;
static ZYReturnGuardRoute ZYReturnGuardCurrentRoute=ZYReturnGuardRouteNone;
static pid_t ZYReturnGuardTapPID=0;

// Shared state touched by both the IMK main thread and event-tap thread.
static std::atomic_bool ZYReturnGuardArmed{false};
static std::atomic_bool ZYReturnGuardEnabled{true};
static std::atomic_bool ZYReturnGuardMainUpPending{false};
static std::atomic_bool ZYReturnGuardPadUpPending{false};
static std::atomic<int> ZYReturnGuardDesiredPID{0};

// Diagnostics are counts only: no key contents are logged or persisted.
static std::atomic<uint64_t> ZYReturnGuardObservedDown{0};
static std::atomic<uint64_t> ZYReturnGuardObservedUp{0};
static std::atomic<uint64_t> ZYReturnGuardReturnDownSeen{0};
static std::atomic<uint64_t> ZYReturnGuardReturnUpSeen{0};
static std::atomic<uint64_t> ZYReturnGuardArmedReturnDown{0};
static std::atomic<uint64_t> ZYReturnGuardSuppressedDown{0};
static std::atomic<uint64_t> ZYReturnGuardSuppressedUp{0};

BOOL ZYReturnGuardPreferenceEnabled(void){
    NSUserDefaults *defaults=[NSUserDefaults standardUserDefaults];
    id value=[defaults objectForKey:ZYStrictReturnGuardKey];
    return value==nil?YES:[value boolValue];
}

BOOL ZYReturnGuardHasAccessibility(void){ return AXIsProcessTrusted(); }

static NSString *ZYReturnGuardRouteName(ZYReturnGuardRoute route){
    switch(route){
        case ZYReturnGuardRoutePerPID:return @"per-PID";
        case ZYReturnGuardRouteAnnotatedSession:return @"annotated-session";
        case ZYReturnGuardRouteSession:return @"session";
        default:return @"未建立";
    }
}

static void ZYReturnGuardTearDown(void){
    // Invalidate the Mach port BEFORE stopping its run loop so WindowServer can
    // never be left waiting on an orphaned active filter.
    CFMachPortRef tap=ZYReturnGuardTap;
    CFRunLoopSourceRef source=ZYReturnGuardSource;
    CFRunLoopRef runLoop=ZYReturnGuardRunLoop;
    ZYReturnGuardTap=NULL;
    ZYReturnGuardSource=NULL;
    ZYReturnGuardRunLoop=NULL;
    ZYReturnGuardThread=nil;
    ZYReturnGuardCurrentRoute=ZYReturnGuardRouteNone;
    ZYReturnGuardTapPID=0;

    if(tap){ CGEventTapEnable(tap,false); CFMachPortInvalidate(tap); }
    if(runLoop&&source)CFRunLoopRemoveSource(runLoop,source,kCFRunLoopCommonModes);
    if(runLoop)CFRunLoopStop(runLoop);
    if(source)CFRelease(source);
    if(tap)CFRelease(tap);
    if(runLoop)CFRelease(runLoop);

    ZYReturnGuardMainUpPending.store(false,std::memory_order_release);
    ZYReturnGuardPadUpPending.store(false,std::memory_order_release);
}

BOOL ZYReturnGuardRequestAccessibility(void){
    NSDictionary *options=@{(__bridge NSString *)kAXTrustedCheckOptionPrompt:@YES};
    BOOL trusted=AXIsProcessTrustedWithOptions((__bridge CFDictionaryRef)options);
    dispatch_async(dispatch_get_main_queue(),^{ ZYReturnGuardRefresh(); });
    return trusted;
}

static void ZYReturnGuardQueueAction(unsigned short keyCode){
    // Never touch the Objective-C input controller on the event-tap thread.
    dispatch_async(dispatch_get_main_queue(),^{
        if(!ZYReturnGuardEnabled.load(std::memory_order_acquire))return;
        ZYReturnGuardHandler handler=ZYReturnGuardHandlerBlock;
        if(handler)handler(keyCode);
    });
}

static void ZYReturnGuardRecoverFromSystemDisable(BOOL timeout){
    dispatch_async(dispatch_get_main_queue(),^{
        ZYReturnGuardLastFailure=timeout?@"Event Tap 曾因逾時停用":@"Event Tap 被系統停用";
        if(ZYReturnGuardTap&&!CFMachPortIsValid(ZYReturnGuardTap))ZYReturnGuardTearDown();
        ZYReturnGuardRefresh();
    });
}

static CGEventRef ZYReturnGuardCallback(CGEventTapProxy proxy,CGEventType type,CGEventRef event,void *userInfo){
    (void)proxy;(void)userInfo;
    if(type==kCGEventTapDisabledByTimeout||type==kCGEventTapDisabledByUserInput){
        ZYReturnGuardRecoverFromSystemDisable(type==kCGEventTapDisabledByTimeout);
        return event;
    }
    if(!event||(type!=kCGEventKeyDown&&type!=kCGEventKeyUp))return event;

    if(type==kCGEventKeyDown)ZYReturnGuardObservedDown.fetch_add(1,std::memory_order_relaxed);
    else ZYReturnGuardObservedUp.fetch_add(1,std::memory_order_relaxed);

    unsigned short keyCode=(unsigned short)CGEventGetIntegerValueField(event,kCGKeyboardEventKeycode);
    BOOL isMain=keyCode==36,isPad=keyCode==76;
    if(!isMain&&!isPad)return event;

    if(type==kCGEventKeyDown)ZYReturnGuardReturnDownSeen.fetch_add(1,std::memory_order_relaxed);
    else ZYReturnGuardReturnUpSeen.fetch_add(1,std::memory_order_relaxed);

    std::atomic_bool *pending=isMain?&ZYReturnGuardMainUpPending:&ZYReturnGuardPadUpPending;
    BOOL wasPending=pending->load(std::memory_order_acquire);

    if(type==kCGEventKeyDown){
        if(!ZYReturnGuardEnabled.load(std::memory_order_acquire))return event;

        // Command/Option/Control Return belongs to the client. Shift+Return remains
        // an IME Return, matching the normal controller path.
        CGEventFlags flags=CGEventGetFlags(event);
        CGEventFlags systemModifiers=kCGEventFlagMaskCommand|kCGEventFlagMaskAlternate|kCGEventFlagMaskControl;
        if(!wasPending&&(flags&systemModifiers))return event;

        BOOL armed=ZYReturnGuardArmed.load(std::memory_order_acquire);
        if(!armed&&!wasPending)return event;

        BOOL autoRepeat=CGEventGetIntegerValueField(event,kCGKeyboardEventAutorepeat)!=0;
        if(wasPending&&autoRepeat){
            ZYReturnGuardSuppressedDown.fetch_add(1,std::memory_order_relaxed);
            return NULL;
        }

        pending->store(true,std::memory_order_release);
        if(armed){
            ZYReturnGuardArmedReturnDown.fetch_add(1,std::memory_order_relaxed);
            ZYReturnGuardQueueAction(keyCode);
        }
        ZYReturnGuardSuppressedDown.fetch_add(1,std::memory_order_relaxed);
        return NULL;
    }

    if(pending->exchange(false,std::memory_order_acq_rel)){
        ZYReturnGuardSuppressedUp.fetch_add(1,std::memory_order_relaxed);
        return NULL;
    }
    return event;
}

static CFMachPortRef ZYCreatePerPIDTap(pid_t pid,CGEventMask mask){
    if(pid<=0||pid==getpid())return NULL;
    return CGEventTapCreateForPid(pid,kCGHeadInsertEventTap,kCGEventTapOptionDefault,mask,ZYReturnGuardCallback,NULL);
}

static CFMachPortRef ZYCreateGlobalTap(CGEventTapLocation location,CGEventMask mask){
    return CGEventTapCreate(location,kCGHeadInsertEventTap,kCGEventTapOptionDefault,mask,ZYReturnGuardCallback,NULL);
}

static BOOL ZYReturnGuardInstallTap(CFMachPortRef tap,ZYReturnGuardRoute route,pid_t tapPID){
    if(!tap)return NO;

    // Keep inert until the dedicated run loop is alive and globals are populated.
    CGEventTapEnable(tap,false);
    CFRunLoopSourceRef source=CFMachPortCreateRunLoopSource(kCFAllocatorDefault,tap,0);
    if(!source){ CFMachPortInvalidate(tap);CFRelease(tap);return NO; }

    dispatch_semaphore_t ready=dispatch_semaphore_create(0);
    __block CFRunLoopRef threadRunLoop=NULL;
    NSThread *thread=[[NSThread alloc] initWithBlock:^{
        @autoreleasepool {
            CFRunLoopRef rl=CFRunLoopGetCurrent();
            CFRetain(rl);
            threadRunLoop=rl;
            CFRunLoopAddSource(rl,source,kCFRunLoopCommonModes);
            dispatch_semaphore_signal(ready);
            CFRunLoopRun();
        }
    }];
    thread.name=@"tw.zhuyin.inputmethod.return-guard";
    thread.qualityOfService=NSQualityOfServiceUserInteractive;
    [thread start];

    if(dispatch_semaphore_wait(ready,dispatch_time(DISPATCH_TIME_NOW,(int64_t)(2*NSEC_PER_SEC)))!=0||!threadRunLoop){
        CFMachPortInvalidate(tap);CFRelease(source);CFRelease(tap);return NO;
    }

    ZYReturnGuardTap=tap;
    ZYReturnGuardSource=source;
    ZYReturnGuardRunLoop=threadRunLoop;
    ZYReturnGuardThread=thread;
    ZYReturnGuardCurrentRoute=route;
    ZYReturnGuardTapPID=tapPID;
    ZYReturnGuardEnabled.store(true,std::memory_order_release);

    CGEventTapEnable(tap,true);
    if(!CGEventTapIsEnabled(tap)){
        ZYReturnGuardTearDown();
        return NO;
    }
    return YES;
}

BOOL ZYReturnGuardEnsureStarted(void){
    if(!ZYReturnGuardPreferenceEnabled()){ZYReturnGuardLastFailure=@"完整防誤送已關閉";return NO;}
    if(!AXIsProcessTrusted()){ZYReturnGuardLastFailure=@"尚未取得輔助使用權限";return NO;}

    pid_t desired=(pid_t)ZYReturnGuardDesiredPID.load(std::memory_order_acquire);

    // A healthy per-PID tap must match the current target. Global fallbacks remain
    // valid, but when a real client PID becomes known we upgrade to per-PID.
    if(ZYReturnGuardTap&&CFMachPortIsValid(ZYReturnGuardTap)){
        BOOL routeMatches=(ZYReturnGuardTapPID==desired);
        if(routeMatches){
            if(!CGEventTapIsEnabled(ZYReturnGuardTap))CGEventTapEnable(ZYReturnGuardTap,true);
            if(CGEventTapIsEnabled(ZYReturnGuardTap)){ZYReturnGuardLastFailure=nil;return YES;}
        }
        ZYReturnGuardTearDown();
    }else if(ZYReturnGuardTap){
        ZYReturnGuardTearDown();
    }

    CGEventMask mask=CGEventMaskBit(kCGEventKeyDown)|CGEventMaskBit(kCGEventKeyUp);

    // 1) Final application-delivery path. This is the preferred route for browser
    // chat because dropping Return here prevents the target app from ever turning
    // that physical key into a DOM key event while we manually advance the IME.
    if(desired>0&&desired!=getpid()){
        if(CFMachPortRef tap=ZYCreatePerPIDTap(desired,mask)){
            if(ZYReturnGuardInstallTap(tap,ZYReturnGuardRoutePerPID,desired)){
                ZYReturnGuardLastFailure=nil;return YES;
            }
        }
    }

    // 2) Session events after they have been annotated for application delivery.
    if(CFMachPortRef tap=ZYCreateGlobalTap(kCGAnnotatedSessionEventTap,mask)){
        if(ZYReturnGuardInstallTap(tap,ZYReturnGuardRouteAnnotatedSession,desired)){
            ZYReturnGuardLastFailure=desired>0?@"per-PID 不可用，已改用 annotated-session":nil;
            return YES;
        }
    }

    // 3) Original build-74 route as last-resort compatibility fallback.
    if(CFMachPortRef tap=ZYCreateGlobalTap(kCGSessionEventTap,mask)){
        if(ZYReturnGuardInstallTap(tap,ZYReturnGuardRouteSession,desired)){
            ZYReturnGuardLastFailure=@"per-PID/annotated 不可用，已退回 session";
            return YES;
        }
    }

    ZYReturnGuardLastFailure=@"已授權，但所有 Event Tap 路徑都建立失敗";
    return NO;
}

void ZYReturnGuardSetTargetPID(pid_t pid){
    if(pid==getpid())pid=0;
    int old=ZYReturnGuardDesiredPID.exchange((int)pid,std::memory_order_acq_rel);
    if(old==(int)pid)return;

    // Main-thread caller: rebuild only when route identity really changes. During
    // ordinary typing the PID remains stable so there is no per-keystroke tap churn.
    if(ZYReturnGuardPreferenceEnabled()&&AXIsProcessTrusted()){
        if(ZYReturnGuardTap)ZYReturnGuardTearDown();
        ZYReturnGuardEnsureStarted();
    }
}

pid_t ZYReturnGuardTargetPID(void){ return (pid_t)ZYReturnGuardDesiredPID.load(std::memory_order_acquire); }
BOOL ZYReturnGuardIsRunning(void){return ZYReturnGuardTap!=NULL&&CFMachPortIsValid(ZYReturnGuardTap);}
BOOL ZYReturnGuardIsArmed(void){return ZYReturnGuardArmed.load(std::memory_order_acquire);}
BOOL ZYReturnGuardIsTapEnabled(void){return ZYReturnGuardTap&&CFMachPortIsValid(ZYReturnGuardTap)&&CGEventTapIsEnabled(ZYReturnGuardTap);}
uint64_t ZYReturnGuardObservedDownCount(void){return ZYReturnGuardObservedDown.load(std::memory_order_relaxed);}
uint64_t ZYReturnGuardObservedUpCount(void){return ZYReturnGuardObservedUp.load(std::memory_order_relaxed);}
uint64_t ZYReturnGuardReturnDownSeenCount(void){return ZYReturnGuardReturnDownSeen.load(std::memory_order_relaxed);}
uint64_t ZYReturnGuardReturnUpSeenCount(void){return ZYReturnGuardReturnUpSeen.load(std::memory_order_relaxed);}
uint64_t ZYReturnGuardArmedReturnDownCount(void){return ZYReturnGuardArmedReturnDown.load(std::memory_order_relaxed);}
uint64_t ZYReturnGuardSuppressedDownCount(void){return ZYReturnGuardSuppressedDown.load(std::memory_order_relaxed);}
uint64_t ZYReturnGuardSuppressedUpCount(void){return ZYReturnGuardSuppressedUp.load(std::memory_order_relaxed);}

NSString *ZYReturnGuardRouteText(void){
    pid_t desired=ZYReturnGuardTargetPID();
    if(ZYReturnGuardCurrentRoute==ZYReturnGuardRoutePerPID)
        return [NSString stringWithFormat:@"路徑：%@ · PID %d",ZYReturnGuardRouteName(ZYReturnGuardCurrentRoute),(int)ZYReturnGuardTapPID];
    if(ZYReturnGuardCurrentRoute!=ZYReturnGuardRouteNone)
        return [NSString stringWithFormat:@"路徑：%@ · 目標 PID %d",ZYReturnGuardRouteName(ZYReturnGuardCurrentRoute),(int)ZYReturnGuardTapPID];
    return [NSString stringWithFormat:@"路徑：尚未建立 · 目標 PID %d",(int)desired];
}

NSString *ZYReturnGuardStatusText(void){
    if(!ZYReturnGuardPreferenceEnabled())return @"Guard：已關閉";
    if(!AXIsProcessTrusted())return @"Guard：等待輔助使用授權";
    if(!ZYReturnGuardTap){
        if(ZYReturnGuardLastFailure.length)return [NSString stringWithFormat:@"Guard：%@",ZYReturnGuardLastFailure];
        return @"Guard：尚未建立 Event Tap";
    }
    if(!CFMachPortIsValid(ZYReturnGuardTap))return @"Guard：Event Tap 已失效，等待重建";
    if(!CGEventTapIsEnabled(ZYReturnGuardTap))return @"Guard：Event Tap 未啟用";
    NSString *route=ZYReturnGuardRouteName(ZYReturnGuardCurrentRoute);
    if(ZYReturnGuardCurrentRoute==ZYReturnGuardRoutePerPID){
        return [NSString stringWithFormat:@"Guard：%@ · PID %d%@",route,(int)ZYReturnGuardTapPID,
            ZYReturnGuardArmed.load(std::memory_order_acquire)?@" · 已武裝":@" · 待命"];
    }
    return [NSString stringWithFormat:@"Guard：%@%@",route,
        ZYReturnGuardArmed.load(std::memory_order_acquire)?@" · 已武裝":@" · 待命"];
}

void ZYReturnGuardRefresh(void){
    BOOL enabled=ZYReturnGuardPreferenceEnabled();
    ZYReturnGuardEnabled.store(enabled,std::memory_order_release);
    if(!enabled){ if(ZYReturnGuardTap)ZYReturnGuardTearDown(); return; }
    if(!AXIsProcessTrusted()){ if(ZYReturnGuardTap)ZYReturnGuardTearDown(); return; }
    ZYReturnGuardEnsureStarted();
}

void ZYReturnGuardSetHandler(ZYReturnGuardHandler handler){
    ZYReturnGuardHandlerBlock=[handler copy];
    if(!handler)ZYReturnGuardArmed.store(false,std::memory_order_release);
}

void ZYReturnGuardSetArmed(BOOL armed){
    BOOL old=ZYReturnGuardArmed.exchange(armed,std::memory_order_acq_rel);
    if(!armed){
        // Keep pending keyUp latches: if keyDown was swallowed just before the IME
        // committed and disarmed, its physical keyUp must still be swallowed.
        return;
    }
    if(!old)ZYReturnGuardRefresh();
}
