---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.2.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    related_skills: [test-driven-development, plan, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## The Feedback Loop Rule

The feedback loop is the debugging work. Before reading code to build a theory, create or identify a **tight** command that can go red on the user's exact symptom and green when the bug is fixed. A tight loop is fast, deterministic, agent-runnable, and specific enough to catch this bug — not merely "doesn't crash".

When a clean repro is hard, spend disproportionate effort building the loop. Guessing without a red-capable loop is the failure mode this skill exists to prevent.

## When to Use

Use for ANY technical issue: test failures, production bugs, unexpected behavior, performance problems, build failures, integration issues.

**Use ESPECIALLY when:** under time pressure, "just one quick fix" seems obvious, already tried multiple fixes, previous fix didn't work, don't fully understand the issue.

**Don't skip when:** issue seems simple, in a hurry, someone wants it fixed NOW (systematic is faster than thrashing).

## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

### 1. Read Error Messages Carefully
- Don't skip past errors or warnings — they often contain the exact solution
- Read stack traces completely; note line numbers, file paths, error codes
- **Action:** Use `read_file` on relevant source files. Use `search_files` to find error string in codebase.

### 2. Build a Tight Feedback Loop
- Can you trigger the user's exact symptom with one command?
- Does it fail for this bug and only pass once fixed?
- Is it fast enough to run repeatedly?
- Is it deterministic? For flaky bugs, can you raise reproduction rate high enough to debug?
- If not reproducible → gather more data, don't guess.

**Ways to construct a loop (try in order):**
1. **Failing test** at the seam reaching the bug (unit/integration/e2e)
2. **HTTP script / curl** against running dev server
3. **CLI invocation** with fixture input, diffing stdout/stderr vs expected
4. **Headless browser script** (Playwright/Puppeteer) asserting DOM/console/network
5. **Replay captured trace**: HAR, request payload, event log, queue message, webhook body
6. **Throwaway harness** booting smallest useful slice calling failing path
7. **Property / fuzz loop** for intermittent wrong output over broad input space
8. **Bisection harness** for `git bisect run` when bug appeared between known states
9. **Differential loop** comparing old vs new version, two configs, providers, datasets
10. **Human-in-the-loop script** only as last resort: script human steps, capture result

**Tighten the loop:**
- Faster: cache setup, narrow scope, skip unrelated init
- Sharper signal: assert exact symptom, not generic success
- More deterministic: pin time, seed randomness, isolate filesystem, freeze network

For non-deterministic bugs: immediate goal = higher reproduction rate. Run trigger 100x, parallelize, add stress, narrow timing windows, inject sleeps. 50% flake = debuggable; 1% flake = usually not.

**Action:** Use `terminal` tool to run tight loop:
```bash
# Specific failing test
pytest tests/test_module.py::test_name -v

# Scripted repro
python scripts/repro_bug.py

# High-repetition flaky repro
for i in {1..100}; do pytest tests/test_flake.py::test_name -q || break; done
```

### 3. Check Recent Changes
- What changed that could cause this? Git diff, recent commits, new dependencies, config changes
- **Action:** `git log --oneline -10`, `git diff`, `git log -p --follow src/problematic_file.py | head -100`

### 4. Gather Evidence in Multi-Component Systems
**WHEN system has multiple components (API → service → database, CI → build → deploy):**

**BEFORE proposing fixes, add diagnostic instrumentation:**
For EACH component boundary:
- Log what data enters the component
- Log what data exits the component
- Verify environment/config propagation
- Check state at each layer

Run once to gather evidence showing WHERE it breaks. THEN analyze to identify failing component. THEN investigate that specific component.

### 5. Trace Data Flow
**WHEN error is deep in call stack:**
- Where does the bad value originate?
- What called this function with the bad value?
- Keep tracing upstream until you find the source
- Fix at the source, not at the symptom

**Action:** Use `search_files` to trace references:
```python
# Find where function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")
```

### Phase 1 Completion Checklist
- [ ] Error messages fully read and understood
- [ ] Tight loop command exists and run at least once
- [ ] Loop is red-capable: asserts user's exact symptom, not nearby failure
- [ ] Loop is deterministic, or flaky bug has high enough reproduction rate
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypotheses can be stated and tested

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

---

## Phase 2: Pattern Analysis

**Find the pattern before fixing:**

### 0. Minimize the Reproduction
Once loop is red, shrink repro to smallest scenario still going red. Cut inputs, callers, config, data, steps **one at a time**, re-running loop after each cut. Keep only what's load-bearing for failure.

Done when removing any remaining element makes loop go green. Minimal repro narrows hypothesis space and often becomes cleanest regression test.

### 1. Find Working Examples
- Locate similar working code in same codebase
- What works that's similar to what's broken?
- **Action:** `search_files("similar_pattern", path="src/", file_glob="*.py")`

### 2. Compare Against References
- If implementing a pattern, read reference implementation COMPLETELY
- Don't skim — read every line
- Understand pattern fully before applying

### 3. Identify Differences
- What's different between working and broken?
- List every difference, however small
- Don't assume "that can't matter"

### 4. Understand Dependencies
- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

---

## Phase 3: Hypothesis and Testing

**Scientific method:**

### 1. Form Ranked Falsifiable Hypotheses
- Generate 3–5 plausible hypotheses before testing any single one
- Rank by likelihood and cheapness to falsify
- State prediction: "If X is cause, then changing/observing Y should make Z happen"
- Discard/sharpen any hypothesis without testable prediction

If user present, show ranked list before testing (they may have domain knowledge that re-ranks). If AFK, proceed with your ranking.

### 2. Test Minimally
- Test highest-ranked hypothesis with smallest possible probe
- Change one variable at a time
- Don't fix multiple things at once
- Prefer debugger/REPL inspection; one breakpoint beats ten logs
- If adding logs, tag every temporary line with unique prefix (`[DEBUG-a4f2]`) for single-search cleanup

### 3. Verify Before Continuing
- Did it work? → Phase 4
- Didn't work? → Form NEW hypothesis
- DON'T add more fixes on top

### 4. When You Don't Know
- Say "I don't understand X"
- Don't pretend to know
- Ask user for help
- Research more

---

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case
- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use `test-driven-development` skill

### 2. Implement Single Fix
- Address root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix
```bash
# Specific regression test
pytest tests/test_module.py::test_regression -v

# Full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — Rule of Three
- **STOP.**
- Count: How many fixes tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture
**Pattern indicating architectural problem:**
- Each fix reveals new shared state/coupling in different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor architecture vs. continue fixing symptoms?

**Discuss with user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question architecture (Phase 4 step 5).

## Common Rationalizations

See `references/tdd-rationalizations.md` for the full table including debugging-specific entries:
- "Issue is simple, don't need process" → Simple issues have root causes too...
- "Emergency, no time for process" → Systematic debugging is FASTER than thrashing...
- "Just try this first, then investigate" → First fix sets the pattern...
- "I'll write test after confirming fix works" → Untested fixes don't stick...
- "Multiple fixes at once saves time" → Can't isolate what worked...
- "Reference too long, I'll adapt the pattern" → Partial understanding guarantees bugs...
- "I see the problem, let me fix it" → Seeing symptoms ≠ understanding root cause...
- "One more fix attempt" (after 2+ failures) → 3+ failures = architectural problem...

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

### Investigation Tools
- **`search_files`** — Find error strings, trace function calls, locate patterns
- **`read_file`** — Read source code with line numbers for precise analysis
- **`terminal`** — Run tests, check git history, reproduce bugs
- **`web_search`/`web_extract`** — Research error messages, library docs

### With delegate_task
See `references/delegate-task-patterns.md` for investigation subagent template.

### With test-driven-development
When fixing bugs:
1. Write test reproducing bug (RED)
2. Debug systematically to find root cause
3. Fix root cause (GREEN)
4. Test proves fix and prevents regression

**Never fix bugs without a test.**

## Real-World Impact

From debugging sessions:
- Systematic: 15-30 minutes to fix
- Random fixes: 2-3 hours thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**