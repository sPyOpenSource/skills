# Skill Curation Manifest and Load Gate

- **Date:** 2026-09-26
- **Status:** Design approved; written spec awaiting user review
- **Scope:** Local curation policy for which skills load into an agent session

## Summary

Decouple the published skill catalog from the set of skills loaded into an agent session. A local `curation.yaml` assigns every skill a tier, and a small script projects the active tier into opencode's `permission.skill` config so that anything not explicitly promoted is denied.

The catalog stays complete on disk and in git, so the repository remains publishable and other consumers are unaffected. Maintenance cost becomes "edit one list": new skills entering the shared catalog are denied by default and therefore create no review obligation.

This spec also resolves the three duplicate skill pairs that currently collide on `name`, making one copy of each unreachable.

## Context

The repository holds 139 skills and is symlinked wholesale into `~/.config/opencode/skills`, so every skill's `name` and `description` are injected into every session — roughly 11,300 tokens of frontmatter before any work begins.

The pain is maintenance, not token count. Responsibilities are implicit: nothing records which of the 139 skills are actually in use, which are worth keeping sharp, or which are merely present. Existing tracking does not help. `.usage.json` covers 72 skills and records a non-zero use count for exactly two (`grill-me`, `hermes-agent`); it is too sparse to drive a curation decision.

Three structural problems compound this:

- **Name collisions.** `systematic-debugging`, `test-driven-development`, and `subagent-driven-development` each exist twice: once at the repository root and once under `software-development/`. opencode matches `permission.skill` patterns against skill `name` and deduplicates on collision, so the `software-development/` copy always wins and the root copy is unreachable. All three root copies are self-contained and free of dangling references, so this is a silent collision, not a broken import.
- **Unintended trims.** Commit `0181439` ("refactor: reduce tokens in software-development skills") rewrote the `software-development/` copies on 2026-08-10, superseding the 2026-06-27 root copies. The trims are clean — no dangling links — so the root copies are stale originals rather than richer variants, with one exception noted below.
- **Inert category stubs.** Six directories contain only a `DESCRIPTION.md` and no skills. Four (`diagramming`, `email`, `gifs`, `smart-home`) are placeholders holding a category description and no body. `inference-sh/DESCRIPTION.md` describes a platform but carries no frontmatter. `domain/DESCRIPTION.md` is a complete, fully front-mattered skill named `domain-intel` that is never loaded, because the file is not named `SKILL.md`.

The curator state confirms the tension: `.curator_state` records `"llm: skipped (consolidation off)"`, meaning automatic consolidation was considered and deliberately switched off.

## Goals

1. Make the set of skills you are responsible for explicit, reviewable, and stored in one file.
2. Ensure a skill added to the shared catalog cannot change your loaded set without a deliberate promotion.
3. Keep the published catalog complete: every installable skill stays in the repository. Removing a name-collided copy is a bug fix, not a reduction, because only one copy of a colliding name was ever loadable.
4. Keep curation reversible in a single edit.
5. Eliminate silent name collisions from the loaded set.
6. Keep the tool and its committed schema example independent of the local manifest, so the repository is usable by anyone who clones it.

## Non-Goals

- Deleting or de-publishing any skill from the shared catalog.
- Reducing token cost as an end in itself.
- Merging overlapping skill families: `grill-me` / `grilling` / `grill-with-docs`, the four design skills (`claude-design`, `sketch`, `prototype`, `popular-web-designs`), the four review skills, or the nine `understand-anything` skills.
- Making `domain-intel` loadable, or cleaning up the inert `DESCRIPTION.md` placeholders.
- Repairing or extending `.usage.json`.
- Any CI gate. Because `curation.yaml` is local and gitignored, `check` is a local command, not a repository hook.
- Changing the hub installer (`.hub/lock.json`), `.bundled_manifest`, or curator backup behavior.

## Approaches Considered

### 1. Tiered manifest plus permission gate — Selected

A local `curation.yaml` assigns each skill a tier via a three-level cascade, and a script writes the active set into `permission.skill` as deny-by-default.

This satisfies the hard constraint — the catalog stays complete — and converts an implicit, memory-based judgment into a reviewable list. It is reversible in one edit, and it makes growth in the shared repo cost nothing.

### 2. Physical split into `catalog/` and `active/`

Repoint the `~/.config/opencode/skills` symlink at an `active/` subtree of symlinks into the catalog, so the loaded set is physically separate from the catalog.

Rejected: it requires a symlink farm, and since opencode discovers `SKILL.md` files several levels deep, a stray file can leak past the gate. It ends up needing the same synchronization script as approach 1, in a worse location.

### 3. Merge and trim the catalog

Merge the overlapping families and delete the duplicates outright, reducing roughly 139 to 110 skills with no gating machinery.

Rejected because it shrinks the published catalog, which is the one constraint that must hold. Its non-controversial subset — resolving the duplicate pairs — is adopted as a separate section below.

## Design

### Tiers and the manifest

A skill is either `active` (loaded, maintained) or `archived` (present, unmaintained). Archived is a legitimate state for a shared catalog, not a verdict on quality.

`curation.yaml` at the repository root resolves tiers through a three-level cascade — **global default → category → individual skill**:

```yaml
default: archived
categories:
  software-development: active
  github: active
  apple: active
  writing-plans: active
skills:
  software-development/code-review-pre-commit: archived
  creative/claude-design: archived
```

Keys under `skills:` are install paths relative to the repository root, so both nested (`creative/p5js`) and top-level (`graphify`) skills are addressable.

A key under `categories:` matches the **first path component** of a skill's install path, and it governs every skill beneath it at any depth — `mlops: active` covers `mlops/research/dspy` and `mlops/inference/llama-cpp`. The same rule covers a top-level directory that is itself a single skill: `writing-plans/SKILL.md` has first component `writing-plans`, so `writing-plans: active` governs it. No special-casing or nested-file inspection is required.

More specific keys always win: a `skills:` entry beats a `categories:` entry, which beats `default`. A path may not appear under both `categories:` and `skills:`.

`default: archived` is the load-bearing decision. A new skill resolves to archived without any edit, so catalog growth creates no review obligation.

The file is gitignored. It encodes personal policy and has no place in a shared collection. A committed `curation.example.yaml` documents the schema so a fresh clone can use the tooling.

### The gate

`permission.skill` in `~/.config/opencode/opencode.jsonc`, which currently has no `permission` block, receives a generated allowlist:

```jsonc
"permission": {
  "skill": {
    // >>> curated by scripts/curate.py — regenerate: python3 scripts/curate.py sync >>>
    "*": "deny",
    "brainstorming": "allow",
    "writing-plans": "allow"
    // <<< curated by scripts/curate.py <<<
  }
}
```

The markers are `//` line comments, which opencode's JSONC parser accepts and the tool never has to strip: it locates the region by text and splices, so the `//` inside a `https://` base URL elsewhere in the file is irrelevant. The region holds only pattern-to-value pairs — no sentinel keys — because `permission.skill` is a schema-validated map whose values must be `allow`, `deny`, or `ask`.

Patterns match skill `name`, not install path, so the tier system collapses to `"*": "deny"` plus one `allow` per active skill. The invariant "not listed means off" is then enforced by opencode rather than held by convention.

The inverse — `"*": "allow"` plus a `deny` per archived skill — was rejected. Its diff is smaller today, but every skill anyone adds to the shared catalog would appear in your sessions, which is the burden this design exists to remove.

Three properties make this safe against a hand-edited config:

- **Surgical rewrite.** The generated block is delimited by marker comments. Only that region is rewritten; hand-written `provider` and `disabled_providers` blocks are left byte-identical.
- **Idempotent.** Running `sync` against an up-to-date config is a no-op, so it is safe to run at any time.
- **Artifact, not source of truth.** `curation.yaml` is the source; the config region is generated. A hand-edit inside the markers is drift, which `check` reports rather than silently accepting.

The gate is local because `permission.skill` is read from a path outside the repository. Other consumers still receive every skill in the catalog; the only reduction is the three unreachable duplicate copies described below, and no loadable skill is withdrawn.

Two failure modes follow from an allowlist and are addressed in the tool: a promoted skill does not take effect until `sync` runs, and a typo in a manifest name is a silent no-op. `check` exists to catch both.

### The tool

`scripts/curate.py`, standard library plus PyYAML — already a soft dependency of the repository's `gate_tests.py`, which skips cleanly when it is absent. Three subcommands:

- **`plan`** — resolve the cascade, print active and archived counts, the active set's total frontmatter size in tokens, and any skill present on disk that appeared since the last recorded review. Recording the review is `plan`'s side effect, which is what makes "I have looked at this list" a checkable fact rather than an assumption.
- **`sync`** — rewrite the marked region from the resolved active set. Idempotent.
- **`check`** — everything `plan` reports, plus manifest consistency and whether the config region matches what `sync` would write. Exits non-zero on any failure. This is the verification entry point.

To detect new skills, a gitignored local stamp file — `.curation_stamp.json` at the repository root — records the skill-set hash at the last `plan`. Without it, "new skills are denied by default" is an unverifiable claim; with it, every `plan` names exactly what changed while you were not looking. This is the mechanism that converts catalog growth from a burden into a non-event. Both `curation.yaml` and `.curation_stamp.json` are added to `.gitignore`.

### Failure handling

Each condition produces a specific message, never a stack trace:

| Condition | Behavior |
|---|---|
| Exception names a skill that does not exist | Error naming the path and the closest matches |
| Two skills resolve to the same `name` | Error listing both install paths; this is the collision case that makes allowlist patterns ambiguous |
| `opencode.jsonc` missing | Error naming the expected path; `sync` never creates the file |
| Marked region absent from `opencode.jsonc` | Error printing the exact skeleton to paste once; the tool never invents JSON structure in a hand-edited file |
| Config region differs from `sync` output | Error naming the drifted skill names; instruct to run `sync` |
| A promoted skill absent from the config region | Error — catches the typo that would otherwise fail silently |
| No manifest present | `plan` and `check` exit non-zero pointing at `curation.example.yaml` |

A collision is an error rather than a warning because it makes the active set ill-defined: the allowlist names a `name`, and two skills answer to it.

### Resolving the duplicate pairs

All three root copies are self-contained; none references the other's files. They are resolved as follows.

- **`systematic-debugging` and `test-driven-development`: delete the root copies.** The `software-development/` versions are the deliberate output of `0181439`, verified free of dangling links to the files being dropped. The root copies are superseded originals. Their extra files (`root-cause-tracing.md`, `defense-in-depth.md`, `find-polluter.sh`, `testing-anti-patterns.md`, and the pressure-test files) leave the repository as a side effect of the earlier trim, and this makes that trim final rather than half-applied.
- **`subagent-driven-development`: keep `software-development/` as canonical and fold the root assets in.** Both copies date to the same commit and use unrelated asset layouts, so there is no evidence of intent. The `software-development/` version is the one that loads today and is consistent with the direction of `0181439`. The root version's three scripts — `review-package`, `sdd-workspace`, `task-brief`, 106 lines of self-contained bash — plus `implementer-prompt.md` and `task-reviewer-prompt.md` are referenced by nothing else in the repository, and they implement exactly the discipline the surviving version already documents in prose as `references/context-budget-discipline.md`. Moving them into the surviving skill preserves working code and pairs an executable implementation with its prose rationale, for about 3 KB. The root directory is then deleted, so the assets are reachable rather than orphaned.

After resolution, the loaded set contains no name collisions. This work lands **before** the first `sync`: `check` treats a collision as an error, so syncing first would produce a config that fails its own verification.

### Rollback

No `permission` block exists in `opencode.jsonc` today, so deleting the marked region restores the current behavior exactly. `curation.yaml` is untracked, so it can be deleted or retained freely. Because `sync` only ever rewrites its own region, the worst case is an incorrect allowlist removable in one edit.

## Verification

Run in this order:

1. `curate.py plan` — counts match intent, and the printed active list is read and signed off, since it is the artifact being approved.
2. `curate.py check` — exits 0. Collisions, missing skills, and config drift all surface here first.
3. Restart opencode and confirm `<available_skills>` lists only active skills. Then attempt to load a denied skill: opencode documents `deny` as both hidden and access-rejected, and the rejection half is worth confirming by hand once.
4. Compare active-set frontmatter tokens against the 11,291-token baseline for all 139 skills.

## Success Criteria

- Active set is 35 skills or fewer.
- The loaded set contains zero name collisions.
- `curate.py check` exits 0.
- A skill added to the catalog is denied until explicitly promoted, verified by adding a throwaway skill and observing it absent from `<available_skills>`.

## Risks

- **An allowlist is brittle by construction.** A promoted skill is inert until `sync` runs, and a mistyped name is a silent no-op. Mitigated by `check`, but the mitigation is a manual step.
- **Editing `opencode.jsonc` by hand can collide with the markers.** Hand edits outside the region are safe; edits inside are drift and are reported as an error.
- **Resolving the duplicates relocates or discards content.** Deleting the two superseded originals finalizes the `0181439` trim, dropping `root-cause-tracing.md`, `defense-in-depth.md`, `find-polluter.sh`, `testing-anti-patterns.md`, and the pressure-test files. The three `subagent-driven-development` scripts move rather than disappear, but they land in a skill whose `SKILL.md` does not currently mention them, so `SKILL.md` must be updated in the same change or they become unreachable in a new place.
- **A large active set would erode the benefit.** If the active list grows toward 139, the manifest becomes overhead with no payoff. The 35-skill criterion is the check on that.
