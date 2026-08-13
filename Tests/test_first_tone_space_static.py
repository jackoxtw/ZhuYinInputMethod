from pathlib import Path

root = Path(__file__).resolve().parents[1]
controller = (root / "App" / "ZYInputController.mm").read_text()
runtime = (root / "App" / "ZYRuntime.mm").read_text()
help_panel = (root / "App" / "ZYCandidatePanel.mm").read_text()

# Space must be contextual: add explicit first tone to an untoned trailing
# Bopomofo syllable, but choose the current candidate after a tone exists.
assert "ZYCompositionNeedsFirstTone" in controller
assert '[_composition appendString:@"ˉ"]' in controller
space_case = controller.split("case 49:", 1)[1].split("case 36:", 1)[0]
assert "ZYCompositionNeedsFirstTone(_composition)" in space_case
assert "chooseSelected:client" in space_case

# The legacy '=' shortcut proposal must not survive. '=' remains punctuation-only.
assert 'case 24:return @"ˉ"' not in controller

# Marked and unmarked first-tone input must share query-learning identity.
assert "0xCB" in runtime and "0x89" in runtime
assert "ZYRuntimeQueryHash" in runtime

# Quick help must explain all five tone symbols and Space semantics.
assert "ˉ ˊ ˇ ˋ ˙" in help_panel
assert "Space" in help_panel and "第一聲" in help_panel

print("test_first_tone_space_static: OK")
