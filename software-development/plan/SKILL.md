---
name: plan
description: Write a markdown plan to .hermes/plans/; no execution.
version: 2.1.0
author: Hermes Agent (writing-craft adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow, design, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Plan Mode

Use this skill when the user wants a plan instead of execution.

## Core Behavior

For this turn, you are **planning only**:
- Do not implement code
- Do not edit project files except the plan markdown file
- Do not run mutating terminal commands, commit, push, or perform external actions
- You may inspect the repo with read-only commands/tools
- Deliverable: markdown plan saved to `.hermes/plans/` in active workspace

## Output Requirements

Write a concrete, actionable markdown plan. Include when relevant:
- Goal
- Current context / assumptions
- Proposed approach
- Step-by-step plan
- Files likely to change
- Tests / validation
- Risks, tradeoffs, open questions

For code tasks: exact file paths, likely test targets, verification steps.

## Save Location

Save with `write_file` under:
```
.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md
```
Relative to active working directory / backend workspace (backend-aware). If runtime provides specific target path, use that.

## Interaction Style

- Request clear enough → write plan directly
- No explicit instruction with `/plan` → infer task from conversation context
- Genuinely underspecified → ask brief clarifying question instead of guessing
- After saving → reply briefly with what you planned and saved path

---

# Writing the Plan Well

The rest of this skill is the craft of authoring a *good* implementation plan.

## Overview

Write comprehensive plans assuming the implementer has **zero context** for the codebase and **questionable taste**. Document everything: which files to touch, complete code, testing commands, docs to check, how to verify. Give bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume implementer is skilled but knows almost nothing about toolset or problem domain. Assume they don't know good test design well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When a Full Implementation Plan Helps

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via `subagent-driven-development`

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement minimal code to pass" — step
- "Run tests to verify pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:
```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:
````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements
Read: feature requirements, design docs/user description, acceptance criteria, constraints

### Step 2: Explore the Codebase
Use Hermes tools:
```python
# Project structure
search_files("*.py", target="files", path="src/")

# Similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Existing tests
search_files("*.py", target="files", path="tests/")

# Key files
read_file("src/app.py")
```

### Step 3: Design Approach
Decide: architecture pattern, file organization, dependencies needed, testing strategy

### Step 4: Write Tasks
Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details
For each task include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but actual code)
- **Exact commands** with expected output
- **Verification steps** proving task works

### Step 6: Review the Plan
Check:
- [ ] Tasks sequential and logical
- [ ] Each task bite-sized (2-5 min)
- [ ] File paths exact
- [ ] Code examples complete (copy-pasteable)
- [ ] Commands exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

## Principles

### DRY (Don't Repeat Yourself)
**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)
**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now
```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)
Every code-producing task includes full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits
Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Vague tasks ("Add authentication") | Specific ("Create User model with email and password_hash fields") |
| Incomplete code ("Add validation function") | Complete code after step description |
| Missing verification ("Test it works") | Exact command + expected output (`pytest tests/test_auth.py -v`, expected: 3 passed) |
| Missing file paths ("Create the model file") | Exact path (`src/models/user.py`) |

## Execution Handoff

After saving the plan:
> "Plan complete and saved. Ready to execute using `subagent-driven-development` — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"

When executing, use `subagent-driven-development`:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**