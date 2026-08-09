# Git Diff Commands Reference

> Shared across: `code-review`, `simplify-code`, `plan`

## Get Diff

```bash
# Default: uncommitted working-tree changes (tracked files)
git diff

# If empty, include staged changes
git diff HEAD

# Scoped variants:
git diff --staged                 # staged changes only
git diff HEAD~1                    # last commit
git diff main...HEAD              # this branch / my PR
git diff -- src/foo.py            # specific file(s)
git diff --name-only              # list changed files only
```

## Baseline Testing (Pre-Commit)

```bash
# Stash changes, run tests, pop
git stash
python -m pytest --tb=no -q 2>&1 | tail -5  # baseline
git stash pop

# Run tests again with changes
python -m pytest --tb=no -q 2>&1 | tail -5

# Compare: only NEW failures block
```

## Security Scan (Added Lines Only)

```bash
# Pattern: grep "^+" for added lines only
git diff --cached | grep "^+" | grep -iE "PATTERN"

# Common patterns:
# Hardcoded secrets
git diff --cached | grep "^+" | grep -iE "(api_key|secret|password|token|passwd)\s*=\s*['\"][^'\"]{6,}['\"]"

# Shell injection
git diff --cached | grep "^+" | grep -E "os\.system\(|subprocess.*shell=True"

# Dangerous eval/exec
git diff --cached | grep "^+" | grep -E "\beval\(|\bexec\("

# Unsafe deserialization
git diff --cached | grep "^+" | grep -E "pickle\.loads?\("

# SQL injection (string formatting in queries)
git diff --cached | grep "^+" | grep -E "execute\(f\"|\.format\(.*SELECT|\.format\(.*INSERT"
```

## Large Diff Handling

```bash
# If diff > 15k chars, split by file
git diff --name-only
git diff HEAD -- specific_file.py
```

## Recent Changes

```bash
# Recent commits
git log --oneline -10

# Uncommitted changes
git diff

# Changes in specific file (with history)
git log -p --follow src/problematic_file.py | head -100
```

## Commit (Verified)

```bash
git add -A && git commit -m "[verified] <description>"
# [verified] prefix = independent reviewer approved
```