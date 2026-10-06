# Skill Index Optimization: Cleanup First, Gate Second

- **Date:** 2026-10-06
- **Status:** Design approved; written spec awaiting user review
- **Scope:** Reduce the always-on skill index from ~139 skills / 11,291 tokens to an enforced active set of ≤35 skills, via a heuristic cleanup pass followed by the curation gate
- **Supersedes:** `2026-09-26-skill-curation-gate-design.md` (mechanism carried forward; non-goals amended, execution order reversed)

## Summary

The always-on `<available_skills>` index — every skill's `name` and `description` — is injected into every session. At 139 skills it costs roughly 11,300 tokens before any work begins, and about half the catalog is dead weight. This project cuts it in two moves:

1. **Cleanup pass (first, no gate):** a heuristic ruleset proposes what to archive and what to rewrite; the user approves the lists; skills move to an in-repo `archive/` with `SKILL.md` renamed so they are undiscoverable, and the worst descriptions are rewritten from an approved batch.
2. **Curation gate (second, over the smaller catalog):** `scripts/curate.py` and a local `curation.yaml` generate a deny-by-default `permission.skill` allowlist in `opencode.jsonc`, with checks extended to enforce the cleanup's invariants permanently.

The cleanup produces the `curation.yaml` content — the heuristic pass's output *is* the active-set list — so no judgment work is duplicated.

## Context

- The skills directory `~/.config/opencode/skills` is a symlink to this repository root, so the whole repo is the discovery root.
- opencode discovers `SKILL.md` files recursively under that root; denied skills are hidden from `<available_skills>` (`permission.skill: deny` = hidden and access-rejected).
- `.usage.json` tracks 72 skills with a non-zero use count for exactly two (`grill-me`, `hermes-agent`) — too sparse to drive pruning. Content heuristics are the decision basis instead.
- The curation gate has a committed design (`2026-09-26`) and a 1,798-line plan (`2026-09-26-skill-curation-gate.md`), but **nothing is implemented**: no `scripts/curate.py`, no `curation.yaml`, not gitignored.
- The working tree already contains half of that plan's duplicate-resolution step (root `systematic-debugging` and `test-driven-development` deleted; `subagent-driven-development` root assets moved into `software-development/`), uncommitted.
- Name collisions exist today: `systematic-debugging`, `test-driven-development`, `subagent-driven-development` each live at the root and under `software-development/`; opencode deduplicates on `name`, so the root copies are unreachable.

## Goals

1. Reduce the always-on index to an active set of **≤35 skills**, measured in frontmatter tokens against the 11,291-token baseline.
2. Make pruning decisions reviewable: heuristics propose, the user approves lists before any file moves.
3. Keep every archived skill recoverable in-repo — nothing deleted except the two superseded duplicate copies.
4. Enforce the result: `curate.py check` must fail if the active set grows past the target, a description bloats, or an archived skill becomes discoverable again.
5. Keep the published catalog usable by anyone who clones it: the tooling and `curation.example.yaml` are committed; `curation.yaml` stays local.

## Non-Goals

- Rewriting skill bodies — only frontmatter `description` is touched in the cleanup.
- Repairing or extending `.usage.json`.
- CI enforcement — `curation.yaml` is local and gitignored, so `check` is a local command, never a repository hook.
- Merging skill families beyond the keep-lists below (no content consolidation).
- Changing the hub installer (`.hub/lock.json`), `.bundled_manifest`, or curator backup behavior.

## Approaches Considered

### 1. Strict two-phase, existing plan verbatim

Execute the 2026-09-26 plan untouched (gate live with an interim active set), then run the cleanup as a second pass and re-sync.

Rejected: the gate gets configured twice with two different active sets, and phase 2 amends a spec that declared catalog completeness and token cost to be non-goals — churn for zero benefit.

### 2. One integrated implementation

Build `curate.py` once with final checks, sync a single time, with the cleanup feeding it directly.

Rejected on ordering: it requires amending the existing 1,798-line plan before any work starts.

### 3. Cleanup first, then gate over the smaller catalog — Selected

Run the heuristic cleanup with no gate in place, then implement the existing gate design over the already-reduced catalog, extending `check` with the cleanup's invariants, and sync exactly once.

Accepted trade-off: there is a short window with no enforcement during cleanup. The operation is local, git-tracked, and single-session, so the exposure is negligible. The cleanup's output (approved active list) seeds `curation.yaml` directly.

## Design

### Phase A — Finish duplicate resolution (Rule 5)

Complete the in-flight working-tree changes per the 2026-09-26 design's duplicate section:

- Delete root `systematic-debugging` and `test-driven-development` copies (superseded by the `software-development/` versions from commit `0181439`).
- Keep `software-development/subagent-driven-development` as canonical; fold the root copy's scripts (`review-package`, `sdd-workspace`, `task-brief`) and prompts (`implementer-prompt.md`, `task-reviewer-prompt.md`) into it, updating its `SKILL.md` to reference them; delete the root directory.

Done when: `git status` shows no duplicate pairs and no two skills share a `name`.

### Phase B — Inventory

A one-off script pass over every `SKILL.md` (or frontmatter block) emits one row per skill: install path, name, description length, frontmatter token count, and flags for each heuristic rule below. This table is the review artifact; no file changes.

### Phase C — Heuristic rules (user approves outputs)

| Rule | Trigger | Action |
|---|---|---|
| 1. Unreachable | Directory has no `SKILL.md` (only `DESCRIPTION.md` or nothing loadable): `diagramming`, `email`, `gifs`, `smart-home`, `inference-sh`, `domain` | Archive (moves as a directory; `domain/DESCRIPTION.md` is flagged as a recoverable hidden skill) |
| 2. Redundancy families | Keep at most: grill family 1 of 3; design family 2 of 4; review family 2 of 4; `understand-anything` 2–3 of 9. *Which* members are kept is decided at list approval, not hard-coded here | Archive the rest |
| 3. Category verdicts | Whole categories the user never reaches for — candidates: `creative`, `media`, `gaming`, `red-teaming` | Every skill in the category joins the **physical** archive list (Phase D); the matching `curation.yaml` cascade entry is written in Phase F. The category list is approved separately from the per-skill lists |
| 4. Broken skills | Active-set skills referencing missing files or dead CLI names | Fix if cheap (pointer edit); archive if rotten |
| 5. Collisions | The three duplicate pairs | Per Phase A — delete/fold, not archive |

The pass produces three lists for approval before any mutation: **archive list**, **active list** (target ≤35), **rewrite list**. Lists may be hand-edited at this stage — heuristics propose, the user disposes.

### Phase D — Archive execution

- Move archived skills to `archive/<original/path>/` (e.g. `archive/creative/p5js/`), preserving path shape so un-archiving is a reverse move.
- Rename each archived `SKILL.md` → `SKILL.md.archived`. The recursive discovery pattern only matches `SKILL.md`, so the file becomes undiscoverable immediately — no gate exists yet, and the rename is what actually removes it from the index.
- Content is untouched; recovery is a reverse rename + move (git history also holds it — moves appear as renames).
- References from active skills to archived skills are rewritten to the kept variant or dropped (caught by Rule 4 before this phase runs).

### Phase E — Description rewrites

- **Offender threshold:** active skills whose frontmatter `description` exceeds **400 characters** (opencode's hard cap is 1,024; the index average is ~80).
- **Target:** one sentence ≤160 characters — a concrete trigger plus the core capability, per opencode's "specific enough for the agent to choose correctly".
- Rewrites are generated as a single **before/after table** (name, old length, new text) and approved in one batch. No silent edits: descriptions are the routing signal.
- Runs after the archive decision, so skills archived by Rules 1–4 are excluded automatically. Archived descriptions are never rewritten.

### Phase F — The curation gate

Mechanism unchanged from `2026-09-26-skill-curation-gate-design.md`: `curation.yaml` (default → categories → skills cascade, gitignored), `scripts/curate.py` with `plan`/`sync`/`check`, marker-delimited `permission.skill` region in `~/.config/opencode/opencode.jsonc`, deny-by-default allowlist, `.curation_stamp.json` new-skill detection, committed `curation.example.yaml`. The 1,798-line plan supplies the implementation steps.

Amendments in this spec:

1. **Order:** built after cleanup, so the first `sync` writes the final active set. No interim config state. The plan's "resolve duplicates before first `sync`" prerequisite is satisfied by Phase A.
2. **Amended non-goals:** the old spec's "no deletion/de-publishing" and "token cost as a non-goal" are superseded — physical archiving to `archive/` is in scope; index token cost is an explicit, measured goal.
3. **Extended `check` assertions** (added to the plan's existing checks):
   - No file named `SKILL.md` exists under `archive/`
   - Active set ≤ 35 skills
   - No active description > 400 characters
   - Active-set frontmatter tokens ≤ the target reported by `plan` (baseline: 11,291)
4. **Two states, one vocabulary:** a *new* catalog skill resolves to `archived` (denied by the gate, files stay in place); a *cleanup-archived* skill is additionally physical (moved + renamed). Both are "not loaded"; only the latter left the published skill tree.
5. **Docs:** the 2026-09-26 design receives a status header pointing here; its plan remains the reference for phase-3 implementation steps rather than being rewritten.

### Error handling

- Every heuristic-rule failure (missing reference, collision, ambiguous keep-choice) surfaces in the Phase B inventory as a flagged row — never silently skipped.
- Phase D/E run only on approved lists; any skill not on a list is untouched.
- `curate.py` inherits the 2026-09-26 design's failure table (missing manifest, drifted config region, typo'd promotion, collision → named errors, never stack traces), plus the four new assertions above.

## Verification

1. Phase A: no duplicate `name` values anywhere in the tree (assert in inventory script).
2. Phase C: archive/active/rewrite lists reviewed and approved by the user.
3. Phase D/E: recount — index tokens drop substantially vs. 11,291; rewrite list matches the approved batch byte-for-byte.
4. `curate.py plan` — active count and token total match intent; active list signed off.
5. `curate.py check` — exits 0 (collisions, drift, archive leak, size caps all enforced here).
6. Restart opencode: `<available_skills>` lists only active skills; a denied skill's load attempt is rejected (hand-checked once).
7. Idempotence: re-running `plan`/`check`/`sync` changes nothing.
8. Promotion drill: add a throwaway skill, observe it absent from `<available_skills>` until promoted + `sync`ed.

## Success Criteria

- Active set ≤ 35 skills; token total measured and reported against the 11,291 baseline.
- Zero name collisions; zero `SKILL.md` files under `archive/`.
- No active description > 400 characters.
- `curate.py check` exits 0 and stays green on re-run.
- Every archived skill recoverable by a reverse move (spot-check three).

## Testing

- `gate_tests.py` (already at repo root) gains `curate.py` coverage: cascade resolution, marker-region splice idempotence, drift detection, each new `check` assertion, collision error path.
- Heuristic rules get fixtures: one synthetic skill positioned to trip each rule, asserting it lands in the proposed list (not merely that the script runs).
- Rewrite batch tool: golden test asserting output table matches the approved input list exactly.

## Risks

- **A bad description rewrite misroutes skills permanently.** Mitigated by the single approved before/after batch; descriptions are never edited outside it.
- **No-gate window during cleanup.** Local, short, git-tracked; worst case is an incomplete move detected by `git status` and Phase F's checks.
- **Heuristics may over-archive.** Every rule outputs a reviewable list before mutation, and archiving is a reversible move — but an over-aggressive category verdict (Rule 3) would be tedious to reverse skill-by-skill. The category list is therefore approved separately from the per-skill lists.
- **The combined spec supersedes two committed docs.** The prior design is annotated with a pointer rather than deleted; the prior plan stays authoritative for implementation detail. Divergence between the two is resolved in this spec where they conflict.
