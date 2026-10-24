from pathlib import Path

root = Path(__file__).resolve().parents[1]
runtime = (root / 'Platforms/macOS/App/ZYRuntime.mm').read_text(encoding='utf-8')
engine_h = (root / 'Shared/Core/ZYEngine.h').read_text(encoding='utf-8')
engine_c = (root / 'Shared/Core/ZYEngine.c').read_text(encoding='utf-8')
runner = (root / 'run_core_tests.sh').read_text(encoding='utf-8')

assert 'uint8_t learned;' in engine_h
assert 'zy_candidate_apply_length_policy' in engine_h
assert 'zy_candidate_apply_length_policy' in engine_c

# Runtime must mark both dictionary learning and phrase learning so the policy
# can append only genuinely learned continuations.
assert 'raw[i].learned=(uint8_t)(learned_count>0);' in runtime
assert 'c.learned=1;' in runtime

# Deduplication must not discard a learned phrase merely because an unlearned
# dictionary row with the same visible word was ranked first.
assert 'if(!deduped[j].learned&&tmp[i].learned)deduped[j]=tmp[i];' in runtime

# The visible candidate list is filtered only after adaptive scoring and dedup.
assert 'zy_candidate_apply_length_policy(deduped,dn,out,cap)' in runtime

# Core regression test must be part of the normal native test runner.
assert 'test_candidate_length_policy.c' in runner
assert 'test_candidate_length_policy' in runner

print('test_native_length_policy_static: OK')
