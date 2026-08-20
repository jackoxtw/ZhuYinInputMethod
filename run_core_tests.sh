#!/bin/sh
set -eu
cd "$(dirname "$0")"
CC=${CC:-cc}
TMP=${TMPDIR:-/tmp}/zhu-yin-native-tests
mkdir -p "$TMP"
$CC -std=c99 -O2 -D_POSIX_C_SOURCE=200809L -I Shared/Core Shared/Core/ZYDictionary.c Shared/Core/ZYEngine.c Shared/Tests/test_engine.c -o "$TMP/test_engine"
$CC -std=c99 -O2 -D_POSIX_C_SOURCE=200809L -I Shared/Core Shared/Core/ZYLearning.c Shared/Tests/test_learning.c -o "$TMP/test_learning"
$CC -std=c99 -O2 -D_POSIX_C_SOURCE=200809L -I Shared/Core Shared/Core/ZYDictionary.c Shared/Core/ZYEngine.c Shared/Tests/test_candidate_learning_ranking.c -o "$TMP/test_candidate_learning_ranking"
$CC -std=c99 -O2 -D_POSIX_C_SOURCE=200809L -I Shared/Core Shared/Core/ZYDictionary.c Shared/Core/ZYEngine.c Shared/Tests/test_candidate_length_policy.c -o "$TMP/test_candidate_length_policy"
$CC -std=c99 -O2 -D_POSIX_C_SOURCE=200809L -I Shared/Core Shared/Core/ZYDictionary.c Shared/Core/ZYEngine.c Shared/Core/ZYComposer.c Shared/Tests/test_composer.c -o "$TMP/test_composer"
$CC -std=c99 -O2 -D_POSIX_C_SOURCE=200809L -I Shared/Core Shared/Core/ZYDictionary.c Shared/Core/ZYEngine.c Shared/Core/ZYComposer.c Shared/Tests/test_composer_workspace.c -o "$TMP/test_composer_workspace"
$CC -std=c99 -O2 -I Shared/Core Shared/Core/ZYConversion.c Shared/Tests/test_conversion.c -o "$TMP/test_conversion"
"$TMP/test_engine" Shared/Resources/dictionary.bin
"$TMP/test_learning" "$TMP/learning"
"$TMP/test_candidate_learning_ranking"
"$TMP/test_candidate_length_policy"
"$TMP/test_composer" Shared/Resources/dictionary.bin
"$TMP/test_composer_workspace" Shared/Resources/dictionary.bin
"$TMP/test_conversion" Shared/Resources/t2s.bin
echo "All native C core tests: OK"
if command -v python3 >/dev/null 2>&1; then
  export PYTHONPATH="Shared/Tools${PYTHONPATH:+:$PYTHONPATH}"
  python3 Tests/test_accessibility_caret_cpp_goto.py
  python3 Tests/test_candidate_position_static.py
  python3 Tests/test_caret_o1_static.py
  python3 Tests/test_script_toggle_static.py
  python3 Tests/test_shortcuts_static.py
  python3 Tests/test_learning_ranking_static.py
  python3 Tests/test_native_length_policy_static.py
  python3 Tests/test_composition_runtime_static.py
  python3 Tests/test_composition_controller_static.py
  python3 Tests/test_composition_build_static.py
  python3 Tests/test_colored_installer.py
  python3 Tests/test_opencc_tw2s_build.py
  python3 Tests/test_build_opencc_tw2s.py
  python3 Tests/test_taiwan_dictionary.py
  python3 Tests/test_build_taiwan_dictionary.py
  python3 Tests/test_release_structure.py
  python3 Tests/test_adaptive_candidate_layout_static.py
  python3 Tests/test_quick_help_static.py
  python3 Tests/test_quick_help_card_style_static.py
  python3 Tests/test_clear_learning_static.py
  python3 Tests/test_clear_learning_nonmodal_static.py
  python3 Tests/test_clear_learning_bottom_anchor_static.py
  python3 Tests/test_candidate_mouse_interaction_static.py
  python3 Tests/test_candidate_delegate_routing_static.py
  python3 Tests/test_mouse_diagnostic_removed_static.py
  python3 Tests/test_candidate_idle_release_static.py
  python3 Tests/test_memory_window_lifecycle_static.py
  python3 Tests/test_memory_drawing_static.py
  python3 Tests/test_peak_memory_static.py
  python3 Tests/test_runtime_allocation_static.py
  python3 Tests/test_memory_diagnostic_modes_static.py
  python3 Tests/test_memory_diagnostic_command_static.py
  python3 Tests/test_candidate_grow_only_static.py
  python3 Tests/test_learning_path_bridge_static.py
  python3 Tests/test_first_tone_space_static.py
  python3 Tests/test_idle_space_caps_shift_static.py
  python3 Tests/test_html_shift_english_static.py
  python3 Tests/test_html_special_candidates_static.py
  python3 Tests/test_html_native_keyboard_parity_static.py
  python3 Tests/test_learned_abbreviation_recall_static.py
  python3 Tests/test_brand_word.py
  python3 Tests/test_brand_recall_static.py
  python3 Tests/test_shared_platform_boundary.py
  python3 Tests/test_macos_layout_static.py
  python3 Tests/test_windows_scaffold_static.py
  python3 Tests/test_cross_platform_paths_static.py
  echo "Candidate caret, Taiwan dictionary, OpenCC tw2s, composition quality, quick-help, and first-tone regression tests: OK"
fi
