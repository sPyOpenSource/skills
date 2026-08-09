---
name: simplify-code
description: "Parallel 4-agent cleanup of recent code changes."
version: 1.2.0
author: Hermes Agent (inspired by Claude Code /simplify)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, cleanup, refactor, delegation, subagent, parallel, simplify]
    related_skills: [requesting-code-review, test-driven-development, plan, code-review-pre-commit]
---

# Simplify Code — Parallel Review & Cleanup

Review recent code changes with four focused reviewers running in parallel, aggregate findings, apply fixes worth applying.

**This is a cleanup pass, not a bug hunt.** Improving quality of code that already works — removing duplication, flattening complexity, cutting waste, deepening band-aid fixes. Correctness bugs → `requesting-code-review`.

**Core principle:** Four narrow reviewers beat one broad reviewer. Each deeply searches for a single problem class — reuse, quality, efficiency, altitude — without diluting attention. They run concurrently: pay latency of one review, not four.

## When to Use

Trigger when user says:
- "simplify" / "simplify my changes" / "simplify these changes"
- "review my code" / "review my recent changes" / "clean up my changes"
- "/simplify" (Claude Code habit)

**Optional modifiers:**
- **Focus:** "simplify focus on efficiency" → run only that reviewer (or weight aggregation). Recognized: `reuse`, `quality`/`simplification`, `efficiency`, `altitude`.
- **Dry run:** "simplify but don't change anything" / "just report" → run reviewers, present findings, apply NOTHING. Ask before applying.
- **Scope:** "simplify the last commit" / "simplify staged" / "simplify src/foo.py" → narrow diff source (see Phase 1).

**Do NOT auto-run** after every edit. Costs four subagents — invoke only when user explicitly asks.

## The Process

### Phase 1 — Identify the Changes

Capture the diff. Default order:

```bash
# 1. Default: uncommitted working-tree changes (tracked files)
git diff

# 2. If empty, include staged changes
git diff HEAD

# 3. Scoped variants:
git diff --staged                 # "staged changes"
git diff HEAD~1                    # "the last commit"
git diff main...HEAD              # "this branch" / "my PR"
git diff -- src/foo.py            # specific file(s)
```

If both empty and no git repo/changes, fall back to files user named or recently edited. If genuinely no changed code, say so and stop.

Capture full diff text. If >2000 changed lines, warn user: four subagents × full diff = token-heavy. Offer to scope down (per-directory, per-commit).

### Phase 2 — Launch Four Reviewers in Parallel

Use `delegate_task` **batch mode** — pass all four tasks in one `tasks` array for concurrency. Four is the right fan-out (within `delegation.max_concurrent_children` budget).

**No delegation available?** (leaf subagent, disabled, budget exhausted): Work through all four angles yourself, sequentially, same standards, same finding format. Note in summary this was inline review, not parallel fan-out.

Give **every** reviewer the **complete diff** (not fragments — cross-file issues hide in gaps) plus absolute repo path for codebase search. Each gets `terminal`, `file`, `search` toolsets.

Tell each reviewer to:
- Search codebase for evidence (don't reason from diff alone)
- **Apply Chesterton's Fence:** before flagging removal, run `git blame` to understand why it exists. If purpose unclear, mark `confidence: low` — don't guess.
- Report findings as structured output:
  ```
  file:line → problem → cost (what's duplicated/wasted/harder to maintain) → suggested fix | confidence: high/medium/low | risk: SAFE/CAREFUL/RISKY
  ```
  The **cost** field forces justification — a finding that can't articulate cost is probably a nit.
  - **SAFE** = proven no behavior change (unused imports, commented-out code, pass-through wrappers). Auto-apply.
  - **CAREFUL** = improves without semantics change (rename local, flatten ternary, extract helper). Apply with test verification.
  - **RISKY** = may change behavior or break public contracts (N+1 restructuring, public API rename, memory lifecycle). Flag for human review — do NOT auto-apply.
- Skip nits and style-only churn. Only flag material improvements.

Pass these four goals (drop any user's focus excludes) — **see `references/simplify-reviewer-prompts.md` for full prompts**:

1. **Code Reuse** — Duplicated functionality already in codebase
2. **Code Quality** — Redundant state, parameter sprawl, copy-paste variation, leaky abstractions, stringly-typed code, nested conditionals, AI slop patterns
3. **Efficiency** — Unnecessary work, missed concurrency, hot-path bloat, TOCTOU, memory issues, broad reads, silent failures
4. **Altitude** — Band-aids on shared infrastructure vs fixes to infrastructure itself

### Phase 3 — Aggregate and Apply

Wait for all four to return (batch mode returns together).

1. **Merge** findings into one list, deduping overlaps (same line/mechanism → collapse).
2. **Discard false positives** — you have most context; drop weak/wrong suggestions silently.
3. **Resolve conflicts.** Default resolution order: **correctness > user's stated focus > readability/reuse > micro-perf.** Don't apply perf fix that hurts clarity unless path genuinely hot. Mutually exclusive defensible suggestions → pick one touching less code, note alternative.
4. **Apply in risk-tier order:**
   - **SAFE first** (auto-apply): unused imports, commented-out code, pass-through wrappers, redundant type assertions. Run tests after.
   - **CAREFUL next** (apply with verification, one file at a time): rename locals, flatten ternaries, extract helpers, consolidate dupes. Run tests after each file. Revert any that break.
   - **RISKY last** (flag for review — do NOT auto-apply): N+1 restructuring, public API changes, concurrency fixes, error-handling changes. Present each with risk description and test coverage status. Altitude findings usually here — present deeper fix, let user decide now vs follow-up.
   - If dry run: present all three tiers, apply nothing.
5. **Verify** no regressions: run targeted tests for touched files (not full suite), re-run linter/type check. If fix breaks test, revert that fix and report.
6. **Summarize** changes: short list grouped by reviewer category and risk tier, plus deliberately skipped findings and why. Note if ran inline (no delegation).

## Pitfalls

See `references/common-pitfalls.md` for comprehensive table including:
- Fan out > 4 / splitting diff across reviewers / reviewers guessing vs searching
- Cleanup becoming rewrite / drifting into bug-hunting / respecting project conventions
- Large diffs blowing context / over-trusting dead code tools
- Renaming public contracts / removing "unnecessary" error handling / not every special case is band-aid

## Related

- `subagent-driven-development`: parallel review *during* implementation, per task. This is standalone *after-the-fact* cleanup.
- `code-review-pre-commit`: pre-commit security/quality gate (bug hunt). This is cleanup.
- `requesting-code-review`: pre-commit verification pipeline.