# Skills Architecture — Resources

## Knowledge

- [OpenCode Agent Skills documentation](https://opencode.ai/docs/skills/)
  Primary source for discovery paths, required frontmatter, name and description rules, the `skill` tool, permissions, and troubleshooting. Use for every claim about how OpenCode discovers and loads skills.

- [OpenCode source repository](https://github.com/anomalyco/opencode)
  Primary implementation reference when the documentation leaves behavior underspecified. Use for checking the current implementation rather than guessing from examples.

- [This repository's `writing-skills` guide](../writing-skills/SKILL.md)
  Local conventions for descriptions, progressive disclosure, information hierarchy, and testing skill instructions. Use for the repository's design principles, not as a replacement for the OpenCode runtime contract.

- [The `opencode` skill](../autonomous-ai-agents/opencode/SKILL.md)
  A concrete example of frontmatter routing text, a procedure, verification criteria, and companion operational guidance. Use for tracing a real skill from selection to execution.

- [The `ask-matt` skill](../ask-matt/SKILL.md)
  A router skill whose body maps situations to other skills. Use when explaining how one skill can direct the agent toward another workflow.

## Wisdom (Communities)

- [OpenCode Discord](https://opencode.ai/discord)
  Community for testing understanding against current agent behavior and asking about edge cases. Prefer questions grounded in a minimal reproducible skill and the official docs.

## Gaps

- OpenCode documents the skill contract and tool boundary, but model-based selection is probabilistic. Lessons should distinguish documented guarantees from useful mental models.
