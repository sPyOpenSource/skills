# Common Pitfalls Reference

> Shared across: `code-review`, `simplify-code`, `systematic-debugging`, `test-driven-development`, `plan`

## Git Diff Issues

| Pitfall | Detection | Resolution |
|---------|-----------|------------|
| **Empty diff** | `git diff --cached` returns nothing | Check `git status`, tell user nothing to verify |
| **Not a git repo** | `git` commands fail | Skip and tell user |
| **Large diff (>15k chars)** | Diff exceeds token budget | Split by file: `git diff --name-only` then `git diff HEAD -- specific_file.py` |
| **No staged changes** | `--cached` empty but `git diff` shows changes | Tell user to `git add <files>` first |

## Tool Failures

| Pitfall | Detection | Resolution |
|---------|-----------|------------|
| **delegate_task returns non-JSON** | Reviewer output not parseable | Retry once with stricter prompt, then treat as FAIL |
| **False positives from reviewer** | Reviewer flags intentional code | Note in fix prompt context; fix agent decides |
| **No test framework found** | Test commands fail silently | Skip regression check; reviewer verdict still runs |
| **Lint tools not installed** | `which ruff/eslint` fails | Skip that check silently, don't fail |

## Auto-Fix Loop Issues

| Pitfall | Detection | Resolution |
|---------|-----------|------------|
| **Auto-fix introduces new issues** | Re-verification fails | Counts as new failure; cycle continues (max 2 attempts) |
| **Fix agent changes unrelated code** | Diff shows unexpected changes | Reject fix; re-prompt with stricter constraints |

## Simplify-Code Specific

| Pitfall | Detection | Resolution |
|---------|-----------|------------|
| **Fan out > 4 reviewers** | More than 4 tasks in batch | Cap at 4; categories cover the space |
| **Splitting diff across reviewers** | Each reviewer gets partial diff | Give WHOLE diff to each; cross-file issues hide in gaps |
| **Reviewers guess instead of search** | Findings lack file:line evidence | Require `file:line` evidence; drop findings without it |
| **Cleanup becomes rewrite** | Edits exceed diff scope | Keep edits to diff + minimal surrounding change |
| **Drift into bug-hunting** | Reviewer finds correctness bugs | Report separately as "found a bug" — different pass |
| **Large diffs blow context** | >2000 changed lines | Scope down before delegating (per-dir, per-commit) |
| **Over-trusting dead code tools** | `knip`/`ts-prune` report unused | Grep for symbol before removing; tools miss dynamic usage |
| **Renaming public contracts** | Export/API/DB/config names changed | Tag as RISKY; never auto-rename public contracts |
| **Removing "unnecessary" error handling** | Empty catch/ignored error flagged | Flag it, don't remove; let human decide |
| **Not every special case is band-aid** | Compat shim/migration/isolation flagged | Check `git blame` and comments; mark `confidence: low` if unclear |

## TDD Specific

| Pitfall | Detection | Resolution |
|---------|-----------|------------|
| **Code before test** | Implementation exists without test | Delete code. Start over with TDD. |
| **Test passes immediately** | First run is green | Test is wrong — testing existing behavior. Fix test. |
| **Test errors (not failures)** | Syntax/typo errors | Fix error, re-run until it fails correctly. |
| **Tests added "later"** | Rationalization detected | Delete code. Start over with TDD. |
| **Horizontal slicing** | All tests written, then all impl | Switch to vertical tracer bullets: RED→GREEN per behavior. |

## General

- **No delegation available** (leaf subagent, disabled, budget exhausted): Work through angles sequentially in this context. Note in summary this was inline review, not parallel fan-out.
- **Respect project conventions**: If repo has AGENTS.md/CLAUDE.md/HERMES.md or linter config, fold those rules into prompts.