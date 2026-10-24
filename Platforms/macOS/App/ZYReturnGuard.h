#import <Foundation/Foundation.h>
#include <stdint.h>
#include <sys/types.h>

NS_ASSUME_NONNULL_BEGIN

typedef void (^ZYReturnGuardHandler)(unsigned short keyCode);

FOUNDATION_EXPORT NSString *const ZYStrictReturnGuardKey;

/// Defaults to YES when the preference has never been written.
BOOL ZYReturnGuardPreferenceEnabled(void);

/// Active-filter event taps require Accessibility permission on macOS.
BOOL ZYReturnGuardHasAccessibility(void);
BOOL ZYReturnGuardRequestAccessibility(void);

/// Creates the best available active-filter route without prompting. Safe to call
/// repeatedly. Route priority is: per-PID -> annotated-session -> session.
BOOL ZYReturnGuardEnsureStarted(void);
BOOL ZYReturnGuardIsRunning(void);
BOOL ZYReturnGuardIsArmed(void);
BOOL ZYReturnGuardIsTapEnabled(void);

/// The IME publishes the frontmost client PID. A per-PID tap is preferred because
/// it filters the event at the final application-delivery path. Passing <= 0 keeps
/// the global annotated/session fallback route.
void ZYReturnGuardSetTargetPID(pid_t pid);
pid_t ZYReturnGuardTargetPID(void);

/// Lightweight counters only; no key contents are recorded. These distinguish
/// "tap receives nothing" from "tap sees Return but composition was not armed".
uint64_t ZYReturnGuardObservedDownCount(void);
uint64_t ZYReturnGuardObservedUpCount(void);
uint64_t ZYReturnGuardReturnDownSeenCount(void);
uint64_t ZYReturnGuardReturnUpSeenCount(void);
uint64_t ZYReturnGuardArmedReturnDownCount(void);
uint64_t ZYReturnGuardSuppressedDownCount(void);
uint64_t ZYReturnGuardSuppressedUpCount(void);

/// Human-readable runtime route and state; intended for the local settings panel.
NSString *ZYReturnGuardStatusText(void);
NSString *ZYReturnGuardRouteText(void);

/// Re-evaluates preference / permission and heals or recreates a dead event tap.
void ZYReturnGuardRefresh(void);

/// Handler is invoked on the main queue after the physical Return keyDown was
/// suppressed. Pass nil when the input controller is no longer active.
void ZYReturnGuardSetHandler(ZYReturnGuardHandler _Nullable handler);

/// Arm only while the IME owns a real/staged composition. The event tap itself stays
/// live and pass-through while idle, eliminating enable/disable timing races.
void ZYReturnGuardSetArmed(BOOL armed);

NS_ASSUME_NONNULL_END
