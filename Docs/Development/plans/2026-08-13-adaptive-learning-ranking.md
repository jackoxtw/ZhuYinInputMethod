# Adaptive Learning Ranking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add capped frequency, event-based recency, and expiring exact-query preference without invalidating existing learning snapshots.

**Architecture:** Keep the persisted structs unchanged. Add event/scoring helpers to `ZYLearning`, make runtime commits begin exactly one event, expose `preference_rank` on candidates, and combine capped learning bonuses during runtime ranking.

**Tech Stack:** C99 core, Objective-C++ InputMethodKit runtime, shell/Python regression tests.

## Global Constraints
- Preserve `ZYLearningPersistent` binary layout and snapshot version 1.
- Learn only on final Enter commit.
- One commit advances `clock` exactly once.
- General candidate frequency cap 31; query cap 8; phrase cap 16.
- General recency lifetime 30 events; query-preferred lifetime 64 events; phrase recency lifetime 32 events.

---

### Task 1: Core learning event and capped scores
**Files:** Modify `Core/ZYLearning.h`, `Core/ZYLearning.c`; test `Tests/test_learning.c`.

- [ ] Add failing tests for one-event clock semantics, capped word/query bonuses, recency decay, and 64-event query preference expiry.
- [ ] Run the C test and confirm RED.
- [ ] Add `zy_learning_begin_event`, capped score helpers, age calculation, and query preference rank.
- [ ] Remove per-record clock increments while preserving count/last persistence.
- [ ] Run the test and confirm GREEN.

### Task 2: Candidate ranking metadata and phrase recency
**Files:** Modify `Core/ZYEngine.h`, `Core/ZYEngine.c`, `App/ZYRuntime.mm`; test `Tests/test_candidate_learning_ranking.c`, `Tests/test_learning_ranking_static.py`.

- [ ] Add failing tests for `preference_rank` ordering and recent-vs-historical score behavior.
- [ ] Run tests and confirm RED.
- [ ] Replace boolean `query_preferred` with `preference_rank` and apply capped word/query/phrase bonuses.
- [ ] Give exact learned phrases rank 1 and live dictionary query preference rank 2.
- [ ] Run tests and confirm GREEN.

### Task 3: Commit-level event boundary and phrase refresh
**Files:** Modify `App/ZYRuntime.h`, `App/ZYRuntime.mm`, `App/ZYInputController.mm`; static test `Tests/test_learning_ranking_static.py`.

- [ ] Add failing static assertions requiring one `ZYRuntimeBeginLearningEvent()` per `learnAndCommit:` and direct refresh of selected user phrases.
- [ ] Run and confirm RED.
- [ ] Begin one learning event at commit start, keep word/combined-phrase records in that event, and refresh a selected learned phrase's count/last.
- [ ] Run and confirm GREEN.

### Task 4: Release validation
**Files:** Modify `App/Info.plist`, `README.md` only if needed for version/docs; run all tests.

- [ ] Bump to v0.1.12 / build 13.
- [ ] Run `./run_core_tests.sh`, shell syntax checks, and Objective-C++ static regression checks.
- [ ] Create ZIP, re-extract it, repeat full verification, and confirm executable bits.
