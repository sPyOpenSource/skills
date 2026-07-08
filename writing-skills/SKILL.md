---
name: writing-skills
description: Use when creating new skills, editing skills, or evaluating skill quality. Covers TDD-based creation, quality principles, vocabulary, and Hermes-agent mechanics.
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, skill-md, quality, testing, design]
    related_skills: [plan, code-review, test-driven-development, codebase-design]
---

This skill has three parts:
1. **Quality Principles** — the vocabulary and design principles that make a skill predictable
2. **TDD Process** — RED-GREEN-REFACTOR for creating skills with subagent testing
3. **Hermes Mechanics** — frontmatter, directory placement, workflow for in-repo skills

Bold terms are defined in [`GLOSSARY.md`](GLOSSARY.md).

---

# Part 1: Quality Principles

A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same _process_ every run, not producing the same output — is the root virtue.

## Invocation

Two choices, trading different costs:

- **Model-invoked** — keeps a **description**, so the agent can fire it autonomously _and_ other skills can reach it. Contributes to **context load**. Omit `disable-model-invocation`, and write a model-facing description with rich trigger phrasing.
- **User-invoked** — strips the description; only you can invoke it. Zero **context load**, but spends **cognitive load**. Set `disable-model-invocation: true`; the description becomes human-facing.

Pick model-invocation only when the agent must reach the skill on its own, or another skill must. When user-invoked skills multiply, cure the cognitive load with a **router skill**.

## Information Hierarchy

Content ranked by how immediately the agent needs it:

1. **In-skill step** — ordered action in SKILL.md. Each step ends on a **completion criterion** (checkable, and where it matters, exhaustive).
2. **In-skill reference** — definition, rule, or fact in SKILL.md, consulted on demand.
3. **External reference** — reference pushed out of SKILL.md, reached by a **context pointer**.

**Progressive disclosure** is the move down the ladder. **Co-location** decides what sits beside it once there.

## Leading Words

A compact concept already in the model's pretraining that anchors behaviour in fewer tokens (e.g. _tracer bullets_, _fog of war_). Repeated throughout, it accumulates a distributed definition. Hunt for opportunities to collapse restatements into a single leading word.

## Pruning

- **Single source of truth**: one authoritative place per meaning.
- **Relevance**: does it still bear on what the skill does?
- **No-op test**: does the sentence change behaviour versus the default? If not, delete it.

## Failure Modes

- **Premature completion** — ending a step before done. Defence: sharpen the completion criterion first; split sequence only if the criterion is irreducibly fuzzy.
- **Duplication** — same meaning in multiple places.
- **Sediment** — stale layers that settle when adding feels safe and removing feels risky.
- **Sprawl** — skill too long even when every line is live. Cure: progressive disclosure and splitting by branch/sequence.
- **No-op** — line that changes nothing because the agent already does it.

---

# Part 2: TDD Process

Writing skills IS Test-Driven Development applied to process documentation.

| TDD Concept | Skill Creation |
|-------------|----------------|
| Test case | Pressure scenario with subagent |
| Production code | Skill document (SKILL.md) |
| Test fails (RED) | Agent violates rule without skill |
| Test passes (GREEN) | Agent complies with skill present |
| Refactor | Close loopholes while maintaining compliance |

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

## When to Create a Skill

**Create when:**
- Technique wasn't intuitively obvious to you
- You'd reference this again across projects
- Pattern applies broadly (not project-specific)

**Don't create for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (put in instructions file)

## Skill Types

- **Technique** — concrete method with steps (condition-based-waiting, root-cause-tracing)
- **Pattern** — way of thinking about problems (flatten-with-flags, test-invariants)
- **Reference** — API docs, syntax guides, tool documentation

## The Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

This applies to NEW skills AND EDITS. Write skill before testing? Delete it. Start over.

## RED: Write Failing Test (Baseline)

Run pressure scenario with subagent WITHOUT the skill. Document exact behavior:
- What choices did they make?
- What rationalizations did they use (verbatim)?
- Which pressures triggered violations?

## GREEN: Write Minimal Skill

Write skill that addresses those specific rationalizations. Run same scenarios WITH skill. Agent should now comply.

## REFACTOR: Close Loopholes

Agent found new rationalization? Add explicit counter. Re-test until bulletproof.

Before full pressure scenarios, **micro-test wording** first: one fresh-context sample per call, include a no-guidance control, 5+ reps per variant, read every flagged match manually.

### Bulletproofing Against Rationalization

**Close every loophole explicitly** — forbid specific workarounds, not just the rule.

**Address "spirit vs letter" arguments** — add "Violating the letter of the rules is violating the spirit of the rules."

**Build rationalization table** — capture excuses from baseline testing:

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Tests after achieve same goals" | Tests-after = "what does this do?" Tests-first = "what should this do?" |

**Create red flags list** — make it easy for agents to self-check when rationalizing.

### Match the Form to the Failure

| Baseline failure | Right form | Wrong form |
|---|---|---|
| Skips rule under pressure | Prohibition + rationalization table + red flags | Soft guidance |
| Wrong-shaped output | Positive recipe: what output IS | Prohibition list |
| Omits required element | Structural: REQUIRED field in template | Prose reminders |
| Behavior depends on condition | Conditional keyed to observable predicate | Unconditional rule + exemption |

**No nuance clauses** — "Don't X unless it matters" reopens the negotiation.

### Skill Discovery Optimization (SDO)

**Description = When to Use, NOT What the Skill Does.**

A description summarizing workflow causes agents to follow the description instead of reading the body. Use only triggering conditions:

```yaml
# GOOD: triggering conditions only
description: Use when executing implementation plans with independent tasks

# BAD: summarizes workflow
description: Use when executing plans - dispatches subagent per task with code review
```

**Keyword coverage** — use words agents search for: error messages, symptoms, synonyms, tool names.

**Descriptive naming** — use active voice, verb-first: `creating-skills` not `skill-creation`.

**Token efficiency** — frequently-loaded skills: <200 words. Others: <500 words. Move details to `--help` or cross-references.

## Testing All Skill Types

- **Discipline-enforcing** (rules): academic questions + pressure scenarios + identify rationalizations
- **Technique** (how-to): application scenarios + variation scenarios + gap testing
- **Pattern** (mental models): recognition + application + counter-examples
- **Reference** (docs): retrieval + application + gap testing

---

# Part 3: Hermes Mechanics

## Frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as first bytes (no leading blank line)
- Closes with `\n---\n` before the body
- Parses as YAML mapping
- `name` field present (≤64 chars, lowercase + hyphens)
- `description` field present (≤1024 chars)
- Non-empty body

Peer-matched shape:

```yaml
---
name: my-skill-name
description: Use when <trigger>.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

## Size Limits

- Description: ≤1024 chars (enforced)
- Full SKILL.md: ≤100,000 chars (enforced)
- Peer skills in `software-development/` sit at 8-14k chars. Past 20k, split into `references/*.md`.

## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
```

Categories: `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `gaming`, `github`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new categories casually.

## Workflow

1. Survey peers in the target category
2. Check validator constraints in `tools/skill_manager_tool.py`
3. Draft with `write_file` to `skills/<category>/<name>/SKILL.md`
4. Validate locally:
   ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 1024
   assert len(content) <= 100_000
   ```
5. `git add` + `git commit` on the active branch

**Note:** The current session's skill loader is cached — new skills won't appear until a new session.

## Cross-Referencing

`metadata.hermes.related_skills` unions both trees (in-repo and `~/.hermes/skills/`). Prefer referencing only in-repo skills from in-repo skills so they work for other clones.

## Editing Existing Skills

- **Small fix:** `skill_manage(action='patch', name=..., old_string=..., new_string=...)`
- **Major rewrite:** `write_file` the whole SKILL.md
- **Adding supporting files:** `write_file` to `skills/<category>/<name>/references/<file>.md`, `templates/<file>`, or `scripts/<file>`
- **Always commit** — in-repo skills are source, not runtime state

## Common Pitfalls

1. Using `skill_manage(action='create')` for an in-repo skill — it writes to `~/.hermes/skills/`, not the repo
2. Leading whitespace before `---` — fails validation
3. Description too generic — should start with "Use when..."
4. Forgetting author/license/metadata — not enforced but peers have it
5. Writing a skill that duplicates a peer — survey before creating
6. Expecting the current session to see the new skill — it won't until a fresh session
7. Letting skills accumulate sediment — should get shorter over time
8. Writing no-op prose — "be careful" rarely changes behaviour
9. Linking to skills that don't exist in-repo — breaks for other clones

## Verification Checklist

- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` present
- [ ] Description ≤1024 chars and starts with "Use when..."
- [ ] Total file ≤100,000 chars (aim for 8-15k)
- [ ] Each ordered step has a checkable completion criterion
- [ ] No-op prose and duplicated rules removed
- [ ] Bulky or branch-specific reference is progressively disclosed
- [ ] Run scenarios WITHOUT skill (baseline) BEFORE writing
- [ ] Run scenarios WITH skill to verify compliance
- [ ] `git add` + `git commit` completed on intended branch
