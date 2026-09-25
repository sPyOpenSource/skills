# Mission: Understand the Skills Architecture

## Why

You want to understand how the skills in this repository are discovered, selected, loaded, and turned into agent behavior. The goal is to reason from the system's contracts instead of treating a skill as a mysterious command or assuming that every metadata field has the same purpose.

## Success looks like

- Trace a request from a `SKILL.md` file on disk to agent behavior
- Distinguish discovery metadata, routing text, loaded instructions, and companion files
- Inspect a real skill and explain why it would match a request
- Diagnose a skill that is missing, hidden, or unlikely to be selected
- Separate OpenCode's runtime contract from this repository's authoring conventions

## Constraints

- Lessons under 10 minutes each
- Use real skill files from this repository
- Prefer tracing a concrete request over abstract model theory
- The learner is new to skills, so build from the existing anatomy and configuration lessons
- Do not teach skill authoring yet; first understand how the system works

## Out of scope

- Writing, testing, or publishing new skills
- Implementing plugins, tools, or model infrastructure
- Speculating about undocumented model internals
