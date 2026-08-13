from pathlib import Path

src = Path("App/ZYCandidatePanel.mm").read_text(encoding="utf-8")

required = [
    "- (NSRect)clearLearningRect",
    "NSHeight(self.bounds)-24.0",
    "NSRect clearLearningRect=self.clearLearningRect;",
    "NSPointInRect(p,self.clearLearningRect)",
]
for needle in required:
    assert needle in src, f"missing bottom-anchor behavior: {needle}"

assert src.count("NSMakeRect(732,86,48,18)") == 0, "clear-learning must not use fixed y=86 geometry"
assert "clearLearningSeparator" in src, "tall candidate panels should visually separate the destructive control"
print("clear learning bottom anchor static test passed")
