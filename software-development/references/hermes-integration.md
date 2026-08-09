# Hermes Integration Reference

> Shared across: all software-development skills

## Running Tests

```python
# RED — verify failure
terminal("pytest tests/test_feature.py::test_name -v")

# GREEN — verify pass
terminal("pytest tests/test_feature.py::test_name -v")

# Full suite — verify no regressions
terminal("pytest tests/ -q")

# With coverage
terminal("pytest tests/ --cov=src --cov-report=term-missing")
```

## Common Test Commands by Language

```bash
# Python (pytest)
python -m pytest --tb=no -q

# Node (npm test)
npm test -- --passWithNoTests

# Rust
cargo test

# Go
go test ./...
```

## Common Lint/Type Check Commands

```bash
# Python
which ruff && ruff check .
which mypy && mypy . --ignore-missing-imports

# Node
which npx && npx eslint .
which npx && npx tsc --noEmit

# Rust
cargo clippy -- -D warnings

# Go
which go && go vet ./...
```

## Search Files (Hermes Tool)

```python
# Find where function is called
search_files("function_name(", path="src/", file_glob="*.py")

# Find where variable is set
search_files("variable_name\\s*=", path="src/", file_glob="*.py")

# Find error string in codebase
search_files("error_message", path="src/")

# Find similar patterns
search_files("similar_pattern", path="src/", file_glob="*.py")
```

## Read File with Line Numbers

```python
read_file("src/module.py", offset=45, limit=30)
```

## Terminal Commands

```python
# Run specific test
terminal("pytest tests/test_module.py::test_name -v")

# High-repetition flaky repro
terminal("for i in {1..100}; do pytest tests/test_flake.py::test_name -q || break; done")

# Git operations
terminal("git log --oneline -10")
terminal("git diff")
terminal("git status")
```

## Delegate Task (Subagents)

See `references/delegate-task-patterns.md` for complete patterns.

Key points:
- Subagent has NO shared context — pass everything explicitly
- Use `toolsets=["terminal", "file", "search"]` for full capability
- Batch mode for parallel: `delegate_task(tasks=[...])`
- Fail-closed for reviewers: unparseable = fail