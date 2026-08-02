---
name: generate-issues
description: Decompose a roadmap phase into a per-phase GitHub-issues file at spec/roadmap/implementation/, ready for /upload-issues.
---

# Skill: Generate Version Issues

Decompose one roadmap **phase** (`vA.B`, e.g. `v0.3`) into a fine-grained,
dependency-ordered **issues file**, written to `spec/roadmap/implementation/`.
The output is the input to `/upload-issues` (which pushes it to GitHub) and then
`/execute-issues` (which implements it).

## Usage

```
/generate-issues <phase>
```

- `/generate-issues 0.2` — decompose roadmap phase **v0.2** → `spec/roadmap/implementation/v0.2-issues.md`
- `/generate-issues v0.5` — phase **v0.5** → `…/v0.5-issues.md`

One file per **phase** (`vA.B`). IDs (`MC-xxx`) are **globally sequential**
and continue across phase files.

## Instructions

### Step 0: Read inputs

1. Normalize the phase to `vA.B` (e.g. `0.2` → `v0.2`).
2. Read [spec/roadmap.md](../../../spec/roadmap.md) §`vA.B` — the phase's
   **Goal**, description, **Tasks**, and **DoD** (plus the referenced `F0.x` /
   Phase 1 acceptance criteria in `spec/far-spec/`).
3. Read [spec/architecture.md](../../../spec/architecture.md) for the
   components and invariants the phase touches, and
   [spec/mission.md](../../../spec/mission.md) for the principles (keyboard
   first, no data loss, single-writer rule, offline degradation,
   confirm-before-run, data-driven UI).
4. Read `CLAUDE.md` (if present) for code conventions and the current module map.
5. **Find the next free `MC-xxx` id:** scan existing
   `spec/roadmap/implementation/v*-issues.md` **and** the legacy
   `spec/roadmap/phase-1-issues.md` (old concept, MC-001…MC-008); continue from
   the highest id used. If none exist, start at `MC-001`.
6. If `…/v{A.B}-issues.md` already exists, ask whether to overwrite or append.

### Step 1: Decompose the phase

Turn the phase's **Tasks** into a small set of issues (typically **3–7**), each
a coherent, independently shippable slice:

- Size each **S** (1–2 d) / **M** (3–5 d) / **L** (5–8 d).
- Order by dependency; the first issue is usually the **gate** (the seam/
  structure everything else builds on).
- Map each issue to part of the phase Tasks; together they must satisfy the
  phase **DoD** and the far-spec acceptance criteria it references.
- **Bake tests into every issue** (MyCom mocks all paid APIs — the Anthropic
  SDK sits behind the `LLMClient` seam — and the `claude` binary is faked in
  tests): unit for pure logic, contract for any seam, a **Pilot-driven**
  integration pass where the DoD is keyboard-reachable behavior.
- A contract change (FileEntry snapshot shape, selection invariants, the
  operation plan/policy seams, keymap registry, theme file format, the
  `LLMClient` seam, state-DB schema) carries a `spec/architecture.md` update +
  its contract test in the **same** issue.
- Stay **within the phase** — don't pull later phases' scope in early
  (mission Non-goals are binding; v2+ features stay in far-spec PHASE2).

### Step 2: Write the issues file

Write `spec/roadmap/implementation/v{A.B}-issues.md` using **exactly** this format:

````markdown
# v{A.B} — GitHub Issues

Issues for phase **v{A.B} — {phase title}** (version **{v0 — MVP | v1 — First
public release}**), derived from the per-phase Tasks in
[roadmap.md](../../roadmap.md) (§v{A.B}) and the components in
[architecture.md](../../../spec/architecture.md) ({the relevant § sections}).
This file is scoped to a single phase; IDs continue from the previous phase
(MC-{prev} → **MC-{first}…{last}**).

{1–3 sentences: what the phase does, the seams it extends, why now.}

## Issues Summary Table

| # | ID | Title | Size | Area | Phase | Dependencies |
|---|----|-------|------|------|-------|--------------|
| 1 | MC-{first} | {title} | M | panels | v{A.B} | -- |
| 2 | MC-{…} | {title} | S | fileops | v{A.B} | MC-{first} |
| … | … | … | … | … | … | … |

**Size legend:** S = 1–2 days, M = 3–5 days, L = 5–8 days
**Areas:** panels · fs · fileops · console · viewer · editor · widgets · keymap · theme · state · platform · ai · claude-code · tests

---

## Dependency Tree

```
MC-{first} ({gate})
  |
  +-- MC-{…} (…) --+
  |                |
  +-- MC-{…} (…) --+
                   |
        MC-{…} (…)  => {phase DoD}
```

**Parallelization hints:** {which gate first; what runs in parallel after}.

---

## v{A.B} — {phase title}

### MC-{id} — {Title}

**Description:**
{1–3 sentences. Note which module(s) it touches: mycom/panels/…, mycom/fileops/…, mycom/ai/….}

**What needs to be done:**
- {bullet}
- {bullet}

**Dependencies:** {MC-ids, or None}

**Expected result:**
{one sentence}

**Acceptance criteria:**
- [ ] {functional criterion, tied to the far-spec F-item where applicable}
- [ ] **Contract test:** {seam pinned} — *(only if a contract changes)*
- [ ] **Unit test:** {pure logic} against **mocks** (no paid/network call)
- [ ] **Pilot test:** {keyboard-driven flow} — *(when the DoD is user-visible behavior)*
- [ ] {ties to the phase DoD}

---

{repeat the `### MC-{id} …` block per issue}

## v{A.B} scope notes

**Total effort:** {rough estimate}.
**Critical path:** MC-{…} → … → MC-{…}.
**Phase DoD (roadmap §v{A.B}):** {restate the DoD}.
**Contracts pinned this phase:** {the seams + their tests}.
**Mock note:** all paid APIs (Anthropic via the `LLMClient` seam) and the
`claude` binary are **mocked/faked** in tests — never a paid or networked call
in CI. Filesystem behavior is tested on tmpfs fixtures, not mocks.
**Companion documents:**
- [roadmap.md](../../roadmap.md) — phase Goal/Tasks/DoD (§v{A.B}).
- [architecture.md](../../../spec/architecture.md) — {the relevant § sections}.
- `spec/far-spec/` — the F-item acceptance criteria this phase implements.
- Generated on upload: `v{A.B}-github-report.md` (MC-xxx → GitHub #), then `v{A.B}-execution-report.md`.
````

### Step 3: Report

Show the user: the file path, the issue count, the `MC-xxx` id range, and
the critical path. Suggest the next step:

```
/upload-issues @spec/roadmap/implementation/v{A.B}-issues.md
```

(Do **not** create GitHub issues here — that's `/upload-issues`. This skill
only writes the local issues file.)

## Important Rules

- **One file per phase** (`vA.B`) at `spec/roadmap/implementation/v{A.B}-issues.md`.
- **IDs are globally sequential** (`MC-xxx`), continuing across phase files **and** the legacy MC-001…MC-008 — never reset per phase.
- **Tests in every issue.** Acceptance criteria include the unit/contract/Pilot tests; paid APIs and the `claude` binary are mocked, never called live.
- **Contract = architecture + test together.** Any contract change lands its `spec/architecture.md` update and contract test in the same issue.
- **Scope to the phase.** Map issues to the phase's Tasks/DoD; honor mission Non-goals — don't pull v2+ features in early.
- **Honor the DoD.** The issues together must satisfy the phase DoD in roadmap §vA.B.
- **Ask on ambiguity.** If the phase's Tasks are unclear or under-specified, ask the user before inventing scope.
- **Don't touch GitHub.** This skill writes only the local file; `/upload-issues` pushes it.
