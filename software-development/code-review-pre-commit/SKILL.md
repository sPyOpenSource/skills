---
name: code-review-pre-commit
description: "Pre-commit verification pipeline: static security scan, baseline-aware quality gates, independent reviewer subagent, auto-fix loop (max 2 cycles)."
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, security, verification, quality, pre-commit, auto-fix]
    related_skills: [subagent-driven-development, plan, test-driven-development, code-review-receiving-feedback, github-code-review]
---

# Pre-Commit Code Review

Automated verification pipeline before code lands. Static scans, baseline-aware quality gates, independent reviewer subagent, auto-fix loop.

**Core principle:** No agent should verify its own work. Fresh context finds what you miss.

## When to Use

- After implementing a feature or bug fix, before `git commit` or `git push`
- When user says "commit", "push", "ship", "done", "verify", or "review before merge"
- After completing a task with 2+ file edits in a git repo
- After each task in subagent-driven-development (two-stage review)

**Skip for:** documentation-only changes, pure config tweaks, or when user says "skip verification".

**This vs `github-code-review`:** This verifies YOUR changes before committing. `github-code-review` reviews OTHER people's PRs on GitHub with inline comments.

## Step 1 — Get the Diff

See `references/git-diff-commands.md`.

```bash
git diff --cached
```

If empty, try `git diff` then `git diff HEAD~1 HEAD`. If `git diff --cached` empty but `git diff` shows changes, tell user to `git add <files>` first. If still empty, run `git status` — nothing to verify.

If diff >15k chars, split by file (see reference).

## Step 2 — Static Security Scan

Scan added lines only. Any match is a security concern fed into Step 5.

See `references/git-diff-commands.md` for commands. See `references/security-patterns.md` for patterns to flag.

## Step 3 — Baseline Tests and Linting

Detect project language and run appropriate tools. Capture failure count BEFORE changes as **baseline_failures** (stash, run, pop). Only NEW failures introduced by your changes block the commit.

See `references/hermes-integration.md` for test and lint commands by language.

**Baseline comparison:** If baseline was clean and your changes introduce failures, that's a regression. If baseline already had failures, only count NEW ones.

## Step 4 — Self-Review Checklist

Quick scan before dispatching reviewer:

- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Input validation on user-provided data
- [ ] SQL queries use parameterized statements
- [ ] File operations validate paths (no traversal)
- [ ] External calls have error handling (try/catch)
- [ ] No debug print/console.log left behind
- [ ] No commented-out code
- [ ] New code has tests (if test suite exists)

## Step 5 — Independent Reviewer Subagent

Call `delegate_task` directly — NOT available inside execute_code or scripts.

Reviewer gets ONLY the diff and static scan results. No shared context with implementer. Fail-closed: unparseable response = fail.

See `references/delegate-task-patterns.md` for the reviewer prompt template.

## Step 6 — Evaluate Results

Combine results from Steps 2, 3, and 5.

**All passed:** Proceed to Step 8 (commit).

**Any failures:** Report what failed, then proceed to Step 7 (auto-fix).

```
VERIFICATION FAILED

Security issues: [list from static scan + reviewer]
Logic errors: [list from reviewer]
Regressions: [new test failures vs baseline]
New lint errors: [details]
Suggestions (non-blocking): [list]
```

## Step 7 — Auto-Fix Loop

**Maximum 2 fix-and-reverify cycles.**

Spawn a THIRD agent context — not you (implementer), not the reviewer. It fixes ONLY the reported issues.

See `references/delegate-task-patterns.md` for the fix agent prompt template.

After fix agent completes, re-run Steps 1-6 (full verification cycle):
- Passed: proceed to Step 8
- Failed and attempts < 2: repeat Step 7
- Failed after 2 attempts: escalate to user with remaining issues; suggest `git stash` or `git reset` to undo

## Step 8 — Commit

If verification passed:

```bash
git add -A && git commit -m "[verified] <description>"
```

The `[verified]` prefix indicates an independent reviewer approved this change.

## Integration with Other Skills

- **subagent-driven-development:** Run this after EACH task as the quality gate (two-stage review: spec compliance + code quality).
- **test-driven-development:** Verifies TDD discipline was followed — tests exist, tests pass, no regressions.
- **plan:** Validates implementation matches plan requirements.

## Pitfalls

See `references/common-pitfalls.md` for comprehensive pitfall table including:
- Empty diff / not a git repo / large diff handling
- delegate_task non-JSON / false positives
- No test framework / lint tools not installed
- Auto-fix introduces new issues