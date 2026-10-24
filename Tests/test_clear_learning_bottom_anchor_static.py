from pathlib import Path

src = Path("Platforms/macOS/App/ZYCandidatePanel.mm").read_text(encoding="utf-8")

required = [
    "- (NSRect)settingsRect",
    "NSHeight(self.bounds)-24.0",
    "NSRect settingsRect=self.settingsRect;",
    "NSPointInRect(p,self.settingsRect)",
]
for needle in required:
    assert needle in src, f"missing bottom-anchor settings behavior: {needle}"

assert src.count("NSMakeRect(732,86,48,18)") == 0, "settings must not use fixed y=86 geometry"
assert "settingsSeparator" in src, "tall candidate panels should visually separate the settings control"
assert 'NSString *settingsLabel=@"設定"' in src
print("settings bottom anchor static test passed")
