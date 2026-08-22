from pathlib import Path

src = (Path(__file__).resolve().parents[1] / 'Platforms/macOS/App/ZYAccessibilityCaret.mm').read_text('utf-8')
fn = src[src.index('static NSRect queryAccessibilityCaretRect(void)'):]
first_goto = fn.index('goto done;')
anchor_decl = fn.index('CGPoint anchor')
assert anchor_decl < first_goto, (
    'Objective-C++ forbids goto from jumping over CGPoint anchor initialization; '
    'declare/initialize anchor before any goto done path'
)
