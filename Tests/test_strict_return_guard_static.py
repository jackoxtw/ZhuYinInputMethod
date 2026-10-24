from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
guard = (ROOT / 'Platforms/macOS/App/ZYReturnGuard.mm').read_text(encoding='utf-8')
header = (ROOT / 'Platforms/macOS/App/ZYReturnGuard.h').read_text(encoding='utf-8')
controller = (ROOT / 'Platforms/macOS/App/ZYInputController.mm').read_text(encoding='utf-8')
panel = (ROOT / 'Platforms/macOS/App/ZYCandidatePanel.mm').read_text(encoding='utf-8')
build = (ROOT / 'Platforms/macOS/scripts/build_and_install.command').read_text(encoding='utf-8')
plist = (ROOT / 'Platforms/macOS/App/Info.plist').read_text(encoding='utf-8')
main = (ROOT / 'Platforms/macOS/App/main.m').read_text(encoding='utf-8')

# Prefer the final application-delivery path, then fall back toward the session stream.
assert 'CGEventTapCreateForPid' in guard
assert 'kCGAnnotatedSessionEventTap' in guard
assert 'kCGSessionEventTap' in guard
assert 'kCGHeadInsertEventTap' in guard
assert 'kCGEventTapOptionDefault' in guard
assert 'CGEventMaskBit(kCGEventKeyDown)' in guard
assert 'CGEventMaskBit(kCGEventKeyUp)' in guard

# Both Return keys are covered and the physical down/up are actually deleted.
assert 'keyCode==36' in guard
assert 'keyCode==76' in guard
assert 'return NULL;' in guard
assert 'kCGEventFlagMaskCommand' in guard
assert 'kCGEventFlagMaskAlternate' in guard
assert 'kCGEventFlagMaskControl' in guard
assert 'ZYReturnGuardMainUpPending' in guard
assert 'ZYReturnGuardPadUpPending' in guard

# Held Return must not advance multiple IME stages.
assert 'kCGKeyboardEventAutorepeat' in guard
assert 'if(wasPending&&autoRepeat)' in guard
assert 'ZYReturnGuardQueueAction(keyCode);' in guard

# Privacy permission must only be requested from explicit UI; controller startup may
# prepare an already-authorized tap but must never raise a permission prompt while typing.
assert 'AXIsProcessTrustedWithOptions' in guard
assert 'ZYReturnGuardEnsureStarted();' in controller
assert 'ZYReturnGuardRequestAccessibility' not in controller
assert 'ZYReturnGuardRequestAccessibility();' in panel
assert '@"授權輔助使用"' in panel
assert '@"完整防誤送"' in panel

# The tap is continuously enabled once authorized, but suppression is armed only while
# the IME owns composition. The existing Return state machine is reused on main.
assert '- (BOOL)returnGuardCompositionActive' in controller
assert 'ZYReturnGuardSetArmed(active);' in controller
assert '[strongSelf consumeReturnWhileComposing:liveClient];' in controller
assert 'ZYReturnGuardSetArmed(NO);' in controller
assert 'ZYReturnGuardSetHandler(nil);' in controller

# Emoji/punctuation candidate modes must publish marked state too; otherwise Return
# could look like an ordinary Enter before the strict guard has permission.
open_start = controller.index('- (void)openSpecialCandidates:')
close_start = controller.index('- (void)closeSpecialCandidates:', open_start)
assert '[self updateMarked:client];' in controller[open_start:close_start]
close_end = controller.index('- (void)showInternalState:', close_start)
assert '[self updateMarked:client];' in controller[close_start:close_end]

# The new source must be part of the actual native build.
assert 'Platforms/macOS/App/ZYReturnGuard.mm' in build
assert 'ZYReturnGuard.o' in build

# Preference is shared by controller/settings code and defaults ON unless explicitly changed.
assert 'ZYStrictReturnGuardKey' in header
assert 'value==nil?YES:[value boolValue]' in guard


# On recent macOS an LSBackgroundOnly process can be denied an active Accessibility
# event tap even when TCC looks granted. Run as an accessory agent instead.
assert '<key>LSBackgroundOnly</key><false/>' in plist
assert '<key>LSUIElement</key><true/>' in plist
assert 'NSApplicationActivationPolicyAccessory' in main

# Diagnostics must prove the tap itself exists/works, not merely AXIsProcessTrusted.
assert 'CGEventTapIsEnabled' in guard
assert 'dedicated CFRunLoop' in guard
assert 'NSThread' in guard
assert 'CFRunLoopRun()' in guard
assert 'CFMachPortIsValid' in guard
assert 'ZYReturnGuardStatusText' in header
assert 'ZYReturnGuardSetTargetPID' in header
assert 'ZYReturnGuardRouteText' in header
assert 'frontmostApplication;' in controller and 'frontmost.processIdentifier' in controller
assert 'per-PID' in guard
assert 'annotated-session' in guard
assert 'ZYReturnGuardRouteText()' in panel
assert 'ZYReturnGuardObservedDownCount' in header
assert 'ZYReturnGuardReturnDownSeenCount' in header
assert 'ZYReturnGuardArmedReturnDownCount' in header
assert 'ZYReturnGuardSuppressedDownCount' in header
assert 'ZYReturnGuardSuppressedUpCount' in header
assert 'fetch_add(1,std::memory_order_relaxed)' in guard
assert 'Tap %llu/%llu' in panel
assert 'Enter %llu/%llu' in panel
assert 'armed %llu' in panel
assert 'drop %llu/%llu' in panel

print('test_strict_return_guard_static: OK')
