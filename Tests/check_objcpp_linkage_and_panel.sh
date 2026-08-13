#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT_CONTROLLER="$ROOT/App/ZYInputController.mm"
if grep -R -nE '\[\[.*\?.*:.*\]\][[:space:]]*setFill' "$ROOT/App" --include='*.m' --include='*.mm'; then
  echo 'Invalid conditional Objective-C message-send syntax remains' >&2
  exit 1
fi
for f in "$ROOT/Core/ZYDictionary.h" "$ROOT/Core/ZYEngine.h" "$ROOT/Core/ZYLearning.h" "$ROOT/Core/ZYConversion.h" "$ROOT/App/ZYRuntime.h"; do
  grep -q '#ifdef __cplusplus' "$f"
  grep -q 'extern "C"' "$f"
done
grep -Fq 'NSEventModifierFlagCommand|NSEventModifierFlagOption|NSEventModifierFlagControl' "$INPUT_CONTROLLER"
grep -Fq 'if(event.modifierFlags&systemModifiers)return NO;' "$INPUT_CONTROLLER"
grep -Fq 'ZYCandidatePanel *_panel;' "$INPUT_CONTROLLER"
grep -Fq '[panel showNearRect:[self clientRect:client]];' "$INPUT_CONTROLLER"
grep -Fq 'NSMaxX(rect)+gap' "$ROOT/App/ZYCandidatePanel.mm"
grep -Fq 'NSPointInRect(anchor,s.frame)' "$ROOT/App/ZYCandidatePanel.mm"
grep -Fq 'BOOL placeBelow=' "$ROOT/App/ZYCandidatePanel.mm"
grep -Fq 'NSMaxY(rect)+gap' "$ROOT/App/ZYCandidatePanel.mm"
grep -Fq 'self.hidesOnDeactivate=NO' "$ROOT/App/ZYCandidatePanel.mm"
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
grep -Fq 'App/ZYCandidatePanel.mm' "$ROOT/build_and_install.command"
grep -Fq 'App/ZYAccessibilityCaret.mm' "$ROOT/build_and_install.command"
grep -Fq -- '-framework ApplicationServices' "$ROOT/build_and_install.command"
grep -Fq -- '-framework CoreFoundation' "$ROOT/build_and_install.command"
grep -Fq 'App/ZYCandidatePanel.mm' "$ROOT/CMakeLists.txt"
grep -Fq 'App/ZYAccessibilityCaret.mm' "$ROOT/CMakeLists.txt"
if grep -Fq 'dispatch_async' "$ROOT/App/ZYAccessibilityCaret.mm"; then
  echo 'Accessibility caret helper must return a fresh rect synchronously' >&2
  exit 1
fi
grep -Fq -- '-framework ApplicationServices' "$ROOT/CMakeLists.txt"
grep -Fq -- '-framework CoreFoundation' "$ROOT/CMakeLists.txt"
echo 'Objective-C++ panel + C linkage regression checks: OK'
