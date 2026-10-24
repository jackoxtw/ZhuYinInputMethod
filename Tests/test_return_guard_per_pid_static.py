from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
guard=(ROOT/'Platforms/macOS/App/ZYReturnGuard.mm').read_text(encoding='utf-8')
header=(ROOT/'Platforms/macOS/App/ZYReturnGuard.h').read_text(encoding='utf-8')
controller=(ROOT/'Platforms/macOS/App/ZYInputController.mm').read_text(encoding='utf-8')
panel=(ROOT/'Platforms/macOS/App/ZYCandidatePanel.mm').read_text(encoding='utf-8')

# Route priority is deterministic: target-app tap first, then annotated, then session.
perpid=guard.index('ZYCreatePerPIDTap(desired,mask)')
annotated=guard.index('kCGAnnotatedSessionEventTap', perpid)
session=guard.index('kCGSessionEventTap', annotated)
assert perpid < annotated < session

# Target PID comes from the foreground application and only a changed PID rebuilds.
assert 'frontmostApplication;' in controller and 'frontmost.processIdentifier' in controller
assert 'ZYReturnGuardSetTargetPID(frontmost.processIdentifier);' in controller
assert 'ZYReturnGuardDesiredPID.exchange' in guard
assert 'if(old==(int)pid)return;' in guard

# All routes are active filters and use the same suppress/manual-IME callback.
assert 'kCGEventTapOptionDefault' in guard
assert 'return NULL;' in guard
assert 'ZYReturnGuardQueueAction(keyCode);' in guard
assert '[strongSelf consumeReturnWhileComposing:liveClient];' in controller

# Runtime diagnostics expose route and target PID.
assert 'ZYReturnGuardRouteText' in header
assert '路徑：' in guard
assert 'PID %d' in guard
assert 'ZYReturnGuardRouteText()' in panel
print('test_return_guard_per_pid_static: OK')
