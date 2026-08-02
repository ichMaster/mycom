---
name: ship-phase
description: Full delivery pipeline over the roadmap. For a version (v0), a phase (v0.2), a range, or an explicit list of phases - RECONCILE with the real implementation, generate-issues, upload-issues, execute-issues, review-and-fix-issues, UPDATE DOCS (README + docs/), release-version A.B.0 (release per PHASE). At the END of the scope, an OPT-IN HARDEN sweep (--harden flag or explicit user approval) fixes the deferred HIGH/MEDIUM findings. Gated; stops on failure; surfaces real decisions.
---

# Skill: Ship Phase — the full delivery pipeline

Drive the entire SDLC loop over the roadmap: **versions contain phases; each phase is released;
the next phase is generated only after the previous one is implemented and fixed** — reconciled
against the real (post-fix) implementation. Hardening of deferred findings is an **opt-in,
end-of-scope** step, never automatic.

> **Terminology (per [spec/roadmap.md](../../../spec/roadmap.md)):** a **version** is a top-level
> roadmap block `vA` (v0 — MVP, v1 — First public release); a **phase** is a `vA.B` block inside
> it, released as `A.B.0` (tag `vA.B.0`). Exception: the pre-pivot release `0.1.0` exists, so phase
> v0.1 (the retrofit) releases as `0.1.1`.

**The loop:**

```
for each PHASE vA.B in scope (roadmap order):
    0. RECONCILE   — ground this phase in the real implementation + all prior fixes
    1. generate-issues vA.B
    2. upload-issues @spec/roadmap/implementation/vA.B-issues.md
    3. execute-issues v{n}::version:{n} --phase vA.B   (implement → validate → commit → push → close)
    4. review-and-fix-issues vA.B          (review → ranked doc → fix-now fixes → same doc)
    5. UPDATE DOCS — README + docs/ reflect the actually implemented code
    6. release-version A.B.0               ← RELEASE PER PHASE (tag vA.B.0)
→ END OF SCOPE: HARDEN (skill: harden-findings) — OPT-IN ONLY (--harden, or ask; skipped otherwise)
→ REPORT to chat (per version block; overall summary for multi-version scopes)
```

This skill is a **thin orchestrator** — it sequences the sub-skills, adds the reconcile gate, the
docs-update gate, and the opt-in hardening sweep, and releases per phase; each sub-skill keeps its
discipline. (For one phase *without* review/docs/release, use `/run-phase` instead.)

> **This pipeline releases.** Invoking `/ship-phase` is the explicit opt-in to the automated
> per-phase releases (real tags + pushes). `release-version`'s own rules still hold — it never
> downgrades and confirms the changelog. To build without releasing, use the individual skills.

## Usage

```
/ship-phase <version|phase|range|list> [--harden]
```

The scope argument accepts four forms:

- **A whole version** — `/ship-phase v0` — every phase in it (v0.1 → v0.2 → … → v0.8), each through
  its six steps incl. its own release; at the end **ask** whether to run the HARDEN sweep; then the
  report to chat.
- **A single phase** — `/ship-phase v0.2` — steps 0–6 for that phase only (incl. its release). No
  HARDEN unless `--harden` is passed or the user approves when asked at the end.
- **A range** — `/ship-phase v0.2-v0.5` — phases v0.2, v0.3, v0.4, v0.5 in order. A version range
  (`v0-v1`) means every phase of both versions.
- **An explicit list** — `/ship-phase v0.2,v0.4,v0.5` (comma- or space-separated) — exactly those
  phases, normalized and executed in **roadmap order** regardless of the order given. Each item
  must resolve to a real roadmap phase.

`--harden` pre-approves the end-of-scope HARDEN sweep (no prompt).

## Instructions

### Step 0: Scope, baseline, and the plan

1. Normalize the argument to an ordered **phase list**: a version (`vA`) expands to its phases from
   [spec/roadmap.md](../../../spec/roadmap.md) (`### vA.B` headings under `## vA`, in file order);
   a range expands inclusively; a list is parsed, normalized (`0.2` → `v0.2`), deduplicated, and
   sorted into roadmap order. Record whether `--harden` was passed.
   - **A list with gaps is legitimate but flag it:** if the list skips phases that are not yet
     released (e.g. `v0.2,v0.5` while v0.3/v0.4 are unbuilt), warn that later phases may depend on
     the skipped ones and get one confirmation before proceeding.
2. Confirm we are on the working branch and the tree is clean; establish a **green baseline**
   (`pytest` + `ruff check`). Never start on a red suite — fix a clear flake first or surface it.
3. **Skip already-shipped phases** (release tag `vA.B.0` — for v0.1, `v0.1.1` — exists). A phase
   partially done (issues/report exist but no tag) resumes from its remaining steps — each
   sub-skill is idempotent (`generate` asks overwrite, `upload` dedupes, `execute` skips closed
   issues, `release` refuses a downgrade).
4. **Confirm the plan once** (phases, label, the six steps and their side effects: GitHub issues,
   one commit per issue pushed to `main`, per-phase release tags), then run — do not re-confirm
   before each sub-step; pause only for the genuine blockers in the rules below.

### Step 1: For each phase — the six steps, gated

Run the phases **strictly in sequence** — phase N+1 starts only after phase N is **released**
(implemented, reviewed, fixed, docs updated, tagged). That sequencing is the point: the next
phase's issues are generated against the previous phase's *real, fixed* implementation. Invoke each
sub-skill via the **Skill tool** (it loads that skill's instructions; follow them fully).

**0. RECONCILE** — the first act of every phase's cycle, carried out **during `generate-issues`
   Step 0**: before decomposing `vA.B`, read (a) the **real current code** of the components it
   touches, (b) prior `spec/roadmap/implementation/*-execution-report.md`, and (c) prior
   `spec/roadmap/implementation/*code-review*.md` — especially their **"Fixes applied"** and
   **"Architecture impact"** notes from review/harden work. Where fixes drifted the code from
   `spec/architecture.md`, the implementation is ground truth; doc corrections ride along in the
   seam-touching issue. This is where "changes in architecture after fixes" enter the next phase's
   issues.
1. **`generate-issues vA.B`** → `spec/roadmap/implementation/vA.B-issues.md` (reconciled, per
   step 0).
2. **`upload-issues @spec/roadmap/implementation/vA.B-issues.md`** → the GitHub issues + labels +
   deps + `vA.B-github-report.md`.
3. **`execute-issues v{n}::version:{n} --phase vA.B`** → implement → validate → commit → **push** →
   close each issue in dependency order (one issue = one commit), then `vA.B-execution-report.md`.
4. **`review-and-fix-issues vA.B`** → code review, the criticality-ranked recommendations doc, the
   **fix-now** fixes only (with regression tests, LLM mocked), results recorded **in that same doc**
   (incl. "Architecture impact" notes). Deferred findings stay deferred — they are the HARDEN
   sweep's input, at the end of the scope, if the user opts in.
5. **UPDATE DOCS** — bring the user-facing documentation in line with what the phase *actually
   shipped*, before the release freezes it:
   - **`README.md`**: features, key bindings, usage, install — only what now really works; remove
     or re-mark anything still aspirational. (The version string itself is bumped by
     `release-version` in the next step.)
   - **`docs/`**: per the project rule, `docs/` documents the **actual implemented code** — add or
     refresh the pages for this phase's functionality (and `mkdocs.yml` nav), verify
     `mkdocs build --strict` passes.
   - Commit as a `docs:` commit. If the phase changed nothing user-visible (pure internals), record
     that explicitly in the commit-less report line instead of inventing doc churn.
6. **`release-version A.B.0`** → bump `VERSION`/`README.md`/`pyproject.toml`/`RELEASE.txt`, tag
   `vA.B.0`, and push. **Release per phase.** (v0.1 releases as `0.1.1` — the retrofit patch on the
   pre-pivot `0.1.0`.)

Gate the hand-offs: upload only after generate wrote the file; execute only after the issues exist;
review only after execute closed the issues with a green report; docs only after the review's
fix-now items are committed; **release only after the docs commit and a green suite**; the **next
phase only after this one is released**.

### Step 2: END OF SCOPE — HARDEN (opt-in only)

When the scope's last phase is released, the deferred 🔴 HIGH / 🟠 MEDIUM findings accumulated in the
run's code-review reports *may* be swept — **but only with explicit user consent**:

- **`--harden` was passed** → the sweep is pre-approved; run it.
- **No flag** → **ask the user now** (one clear question at the scope boundary, listing the
  outstanding HIGH/MEDIUM findings and their sources): run the hardening sweep, or skip? **If
  declined — or no approval is available — skip the sweep entirely.**
- **Never run HARDEN un-asked.** Skipped findings simply remain deferred to their documented homes
  (e.g. v1.3) and are listed in the report.

**When approved, delegate the sweep to the dedicated skill:** invoke **`harden-findings <scope>
--release`** via the Skill tool and follow its instructions fully. That skill collects the run's
code-review reports, fixes every still-unfixed 🔴 HIGH / 🟠 MEDIUM finding (🟡 LOW stays deferred) —
each with a regression test, validated green, one focused commit — updates the reports in place
("Fixes applied" + "Architecture impact", which the next phase's RECONCILE reads), refreshes
README/docs if behavior changed, and, because the scope's phases are already released, ships the
result as a **`C` patch release** on the scope's latest phase (e.g. `v0.8.1`). Its escape hatch (a
fix that can't land safely is held with a reason and surfaced) applies unchanged.

### Step 3: REPORT to chat

After the scope (and its HARDEN sweep, if approved), **report to chat** (not a file):
- **Per phase:** MC id range → GitHub #s, execution commit range + test/lint status, review finding
  counts (**fixed-now / deferred**, with homes), any **Architecture impact** deltas, the docs
  updated (README/docs pages, or "no user-visible change"), and the release tag.
- **HARDEN outcome:** ran (which findings were fixed, the patch tag) / declined / not offered —
  plus the still-outstanding HIGH/MEDIUM findings and their homes if skipped.
- **Rollup:** what the scope delivered against its roadmap goal(s).

For a multi-version scope, group the per-phase lines under their version and add a short **overall
summary** (phases shipped, phases skipped as already-released, anything stopped early and what
remains, what's next).

## Important Rules

- **Release per PHASE (`A.B.0`)** — after that phase is built, reviewed, its fix-now items fixed,
  and its docs updated. Never batch several phases into one release; never release mid-phase.
- **Docs before the tag.** Step 5 is a gate, not a suggestion: a release never ships with a README
  or `docs/` that describe code that doesn't exist (or omit code that does). `docs/` documents the
  actual implementation only — design stays in `spec/`.
- **HARDEN is end-of-scope and OPT-IN only.** It runs solely when `--harden` was passed or the user
  explicitly approves at the boundary. Never run it unrequested; when skipped, the deferred
  HIGH/MEDIUM findings stay in their documented homes and are surfaced in the report. When it does
  run and lands fixes, ship them as a `C` patch release on the scope's latest phase.
- **Next phase only after the previous is released.** The strict sequencing is what makes the
  RECONCILE step meaningful: phase N+1's issues are generated against phase N's real, fixed code.
- **Reconciliation is step 0 of every phase** (during `generate-issues` Step 0): real code +
  execution reports + review docs' "Fixes applied"/"Architecture impact" are the input to the next
  phase's issues; `spec/architecture.md` corrections ride along in seam-touching issues.
- **Sequential and gated.** Each step's output is the next step's input. Never start a step whose
  predecessor didn't finish cleanly; never interleave two phases' pipelines.
- **Stop on failure — do not paper over it.** If any sub-skill fails, or any fix hits a red
  `pytest`/`ruff`, halt, report what completed and what remains, and let the user decide. Never
  release a phase whose suite isn't green.
- **Every fix ships a regression test**, the LLM is always mocked (the `LLMClient` seam), the
  `claude` binary is faked, and the suite stays green and deterministic.
- **Surface real decisions.** Pause for an **overwrite/append** prompt, a **gapped phase list**
  (unreleased dependencies skipped), the **HARDEN approval question**, a held finding, or any
  execution/validation failure. Routine plan confirmations run straight through.
- **Delegate, never duplicate.** This skill only sequences the sub-skills (`generate-issues`,
  `upload-issues`, `execute-issues`, `review-and-fix-issues`, `harden-findings`,
  `release-version`) and adds the gating plus the docs step; no other logic of its own. Each
  sub-skill keeps its discipline — one issue = one commit, seam changes carry
  `spec/architecture.md` + contract test, IDs stay in the `MC-xxx` namespace.
- **Ask on a bad target.** If any argument doesn't resolve to a real roadmap version or phase, ask.
