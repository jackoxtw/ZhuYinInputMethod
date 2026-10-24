#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT_CONTROLLER="$ROOT/Platforms/macOS/App/ZYInputController.mm"
if grep -R -nE '\[\[.*\?.*:.*\]\][[:space:]]*setFill' "$ROOT/Platforms/macOS/App" --include='*.m' --include='*.mm'; then
  echo 'Invalid conditional Objective-C message-send syntax remains' >&2
  exit 1
fi
for f in "$ROOT/Shared/Core/ZYDictionary.h" "$ROOT/Shared/Core/ZYEngine.h" "$ROOT/Shared/Core/ZYLearning.h" "$ROOT/Shared/Core/ZYConversion.h" "$ROOT/Platforms/macOS/App/ZYRuntime.h"; do
  grep -q '#ifdef __cplusplus' "$f"
  grep -q 'extern "C"' "$f"
done
grep -Fq 'NSEventModifierFlagCommand|NSEventModifierFlagOption|NSEventModifierFlagControl' "$INPUT_CONTROLLER"
grep -Fq 'if(event.modifierFlags&systemModifiers)return NO;' "$INPUT_CONTROLLER"
grep -Fq 'ZYCandidatePanel *_panel;' "$INPUT_CONTROLLER"
grep -Fq '[panel showNearRect:[self clientRect:client]];' "$INPUT_CONTROLLER"
grep -Fq 'NSMaxX(rect)+gap' "$ROOT/Platforms/macOS/App/ZYCandidatePanel.mm"
grep -Fq 'NSPointInRect(anchor,s.frame)' "$ROOT/Platforms/macOS/App/ZYCandidatePanel.mm"
grep -Fq 'BOOL placeBelow=' "$ROOT/Platforms/macOS/App/ZYCandidatePanel.mm"
grep -Fq 'NSMaxY(rect)+gap' "$ROOT/Platforms/macOS/App/ZYCandidatePanel.mm"
grep -Fq 'self.hidesOnDeactivate=NO' "$ROOT/Platforms/macOS/App/ZYCandidatePanel.mm"
grep -Fq '[_panel orderOut:nil]' "$INPUT_CONTROLLER"
grep -Fq -- '- (BOOL)moveSelectionTo:(NSUInteger)index client:(id)client' "$INPUT_CONTROLLER"
grep -Fq 'case 123: return _candidateCount?' "$INPUT_CONTROLLER"
grep -Fq -- '- (void)deactivateServer:(id)sender' "$INPUT_CONTROLLER"
grep -Fq '[super deactivateServer:sender]' "$INPUT_CONTROLLER"
grep -Fq 'attributesForCharacterIndex:' "$INPUT_CONTROLLER"
grep -Fq 'lineHeightRectangle:&lineRect' "$INPUT_CONTROLLER"
if grep -Fq 'NSEvent.mouseLocation' "$INPUT_CONTROLLER"; then
  echo 'Mouse pointer must not be used as a caret-position fallback' >&2
  exit 1
fi
grep -Fq '#import "ZYAccessibilityCaret.h"' "$INPUT_CONTROLLER"
grep -Fq 'ZYAccessibilityCaretRect()' "$INPUT_CONTROLLER"
grep -Fq 'NSRange caret=NSMakeRange(NSNotFound,0);' "$INPUT_CONTROLLER"
grep -Fq 'NSRange marked=[client markedRange];' "$INPUT_CONTROLLER"
grep -Fq 'caret=NSMakeRange(NSMaxRange(marked),0);' "$INPUT_CONTROLLER"
grep -Fq 'NSRange selected=[client selectedRange];' "$INPUT_CONTROLLER"
grep -Fq 'showNearRect:' "$INPUT_CONTROLLER"
grep -Fq 'static BOOL isASCIIEnglishLetter(NSString *text)' "$INPUT_CONTROLLER"
grep -Fq 'static NSInteger shiftSlot(unsigned short k)' "$INPUT_CONTROLLER"
grep -Fq 'if(_candidateCount&&shift){NSInteger slot=shiftSlot(event.keyCode);' "$INPUT_CONTROLLER"
grep -Fq 'if(shift&&isASCIIEnglishLetter(event.characters))' "$INPUT_CONTROLLER"
grep -Fq '[client insertText:latin replacementRange:NSMakeRange(NSNotFound,NSNotFound)];return YES;' "$INPUT_CONTROLLER"
INSTALLER="$ROOT/Platforms/macOS/scripts/build_and_install.command"
grep -Fq 'Platforms/macOS/App/ZYCandidatePanel.mm' "$INSTALLER"
grep -Fq 'Platforms/macOS/App/ZYAccessibilityCaret.mm' "$INSTALLER"
grep -Fq -- '-framework ApplicationServices' "$INSTALLER"
grep -Fq -- '-framework CoreFoundation' "$INSTALLER"
grep -Fq 'Platforms/macOS/App/ZYCandidatePanel.mm' "$ROOT/CMakeLists.txt"
grep -Fq 'Platforms/macOS/App/ZYAccessibilityCaret.mm' "$ROOT/CMakeLists.txt"
if grep -Fq 'dispatch_async' "$ROOT/Platforms/macOS/App/ZYAccessibilityCaret.mm"; then
  echo 'Accessibility caret helper must return a fresh rect synchronously' >&2
  exit 1
fi
grep -Fq -- '-framework ApplicationServices' "$ROOT/CMakeLists.txt"
grep -Fq -- '-framework CoreFoundation' "$ROOT/CMakeLists.txt"
echo 'Objective-C++ panel + C linkage regression checks: OK'
