from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / 'Platforms/macOS/App/ZYInputController.mm').read_text('utf-8')

start = controller.index('- (NSRect)clientRect:(id)client')
end = controller.index('\n- (void)updateMarked:', start)
method = controller[start:end]

assert '@autoreleasepool' in method, 'caret lookup should release temporary AppKit objects within the key event'
assert 'for(;cursor>=0;cursor--)' not in method, 'caret lookup must not scan backward through the whole preedit string'
assert 'while(cursor' not in method, 'caret lookup must remain O(1), not loop across preedit characters'
assert 'attributesForCharacterIndex:(NSUInteger)cursor lineHeightRectangle:&lineRect' in method, 'must query only the final inline character through IMK'
assert method.count('attributesForCharacterIndex:(NSUInteger)cursor lineHeightRectangle:&lineRect') == 1, 'IMK line-height lookup must be invoked once per caret lookup'
assert method.index('attributesForCharacterIndex:') < method.index('firstRectForCharacterRange:'), 'IMK lookup must remain the primary caret source'
assert method.index('firstRectForCharacterRange:') < method.index('ZYAccessibilityCaretRect()'), 'document-range fallback must remain ahead of AX fallback'
