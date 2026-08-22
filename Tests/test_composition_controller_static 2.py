from pathlib import Path

s = (Path(__file__).resolve().parents[1] / 'Platforms' / 'macOS' / 'App' / 'ZYInputController.mm').read_text()
assert 'if(c.segment_count)' in s
assert 'c.segment_ids[j]' in s
assert 'c.segment_consume_codepoints[j]' in s
assert 'ZYRuntimeCandidateWord' in s
assert 'ZYRuntimeCandidatePron' in s
append_pos = s.index('- (BOOL)appendPieceForCandidate:')
learn_pos = s.index('- (void)learnAndCommit:')
segment_pos = s.index('if(c.segment_count)', append_pos)
assert append_pos < segment_pos < learn_pos
# Selection expansion stages pieces only; learning remains centralized in final commit.
assert 'ZYRuntimeLearnWord' not in s[append_pos:learn_pos]
assert 'ZYRuntimeLearnPhrase' not in s[append_pos:learn_pos]
print('test_composition_controller_static: OK')
