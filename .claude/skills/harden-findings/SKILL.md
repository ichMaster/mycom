---
name: harden-findings
description: Sweep the code-review reports in spec/roadmap/implementation/ for still-unfixed HIGH/MEDIUM findings, fix each with a regression test, update the reports in place, and (opt-in) ship the result as a patch release. Runs standalone, or invoked by /ship-phase after user approval.
---

# Skill: Harden Findings

Close out the serious code-review findings that were **deferred** ("real, but not recommended for
immediate fix"): sweep the review reports, fix every remaining **🔴 HIGH / 🟠 MEDIUM** finding with a
regression test, record the results in the same reports, and optionally cut a `C` patch release so
the hardening actually ships.

Invoking this skill **is** the user's consent to harden — it never runs implicitly. (`/ship-phase`
invokes it only after its own `--harden` flag or an explicit user approval at the version boundary.)

## Usage

```
/harden-findings [scope] [--release]
```

- `scope` — optional filter: a version (`v0` → reports whose findings belong to that version's
  code), a phase (`v0.2`), or omitted → **all** `spec/roadmap/implementation/*code-review*.md`
  reports.
- `--release` — after fixes land, cut the `C` patch release automatically (e.g. `0.3.0` → `0.3.1`,
  tag `v0.3.1`; note v0.1 released as `0.1.1`, so its patch is `0.1.2`). Without it, finish by
  **recommending** `/release-version` — never bump a version without explicit confirmation.

Examples: `/harden-findings` · `/harden-findings v0` · `/harden-findings v0.4 --release`

## Instructions

### Step 0: Baseline and the finding list

1. Confirm the working branch and a clean tree; establish a **green baseline** (`pytest` +
   `ruff check`). Never harden on a red suite — fix a clear flake first (own commit) or surface it.
2. **Collect** the code-review reports: `spec/roadmap/implementation/*code-review*.md`, filtered by
   `scope` if given.
3. **Select** every finding with severity **🔴 HIGH or 🟠 MEDIUM** whose **Status is not FIXED**
   (pending/`⏳ deferred`) — **regardless of its `DEFER → <home>` recommendation**. Ignore 🟡 LOW
   (it stays deferred to its documented home). Order the queue **HIGH before MEDIUM**, then by
   report.
4. Show the queue (finding, severity, source report, proposed fix) — then proceed. If the queue is
   empty, say so and stop.

### Step 1: Fix each finding, gated

For each finding in order:

1. **Implement the fix** following `CLAUDE.md` + `spec/architecture.md`. Keep it minimal and
   focused — one finding, one change.
2. **Add a regression test that would have caught the bug** (a data-loss finding gets a
   cancelled-mid-tree tmpfs test, a single-writer finding gets a worker/UI test, a keymap finding
   gets a Pilot key-press test, …). The **LLM is always mocked** (the `LLMClient` seam) and the
   `claude` binary is faked — no paid or networked call.
3. **Validate:** `pytest` (green, deterministic) + `ruff check`. Only commit code that passes.
4. **Commit** one focused change referencing the finding (`fix(<area>): … (code review #N)`), with
   the `Co-Authored-By` trailer. A **seam change** (FileEntry shape, selection invariants,
   plan/policy seams, keymap registry, theme format, `LLMClient`, state-DB schema) carries its
   `spec/architecture.md` update **and** contract test in the same commit.
5. **Update the source report in place:** flip the finding's **Status** to `✅ FIXED — <commit>`,
   extend its **"Fixes applied"** section (change, test, verification), and add an **"Architecture
   impact"** note if the fix changed documented behavior/contracts — the next `/generate-issues`
   reconciliation reads exactly these notes. If the finding was homed to a *later* roadmap item
   (e.g. v1.3 error recovery), note there that this scope is **already addressed** so it isn't
   re-done.

**Escape hatch:** if a fix genuinely can't land safely now (needs a design decision, or would
balloon into a large change), **do not force a broken or half-baked fix** — leave the finding
deferred, record *why* it's held in the report, and surface it to the user. Prefer fixing; hold
only when a clean landing isn't possible.

### Step 2: Final validation + optional patch release

1. Re-run the **full suite** once after the sweep — green and deterministic — plus `ruff check`.
2. **Docs check:** if any fix changed user-visible behavior (a key, a dialog, a default, a config
   flag), update `README.md` and the affected `docs/` pages **before** releasing — `docs/`
   documents the actual code, and a patch release must not ship with stale docs.
3. Commit the report (and docs) updates (a `docs:` commit) and push everything.
4. **Release:** if `--release` was passed (or the user confirms when asked), invoke
   `release-version` for the `C` patch bump on the affected released phase (the roadmap's
   "post-release fix", e.g. `0.4.0` → `0.4.1`, tag `v0.4.1`). Otherwise just recommend the command
   and stop — releasing stays explicit.

### Step 3: Report to chat

Summarize: findings fixed (severity, commit each), findings **held** via the escape hatch (with
why), LOW findings untouched (with homes), final suite/lint status, docs updated (or not needed),
and the patch tag (or the recommended `/release-version` command).

## Important Rules

- **Only HIGH and MEDIUM.** LOW findings are out of scope — they stay deferred to their documented
  homes.
- **Invocation = consent.** This skill never runs implicitly; orchestrators must obtain explicit
  user approval (a flag or a question) before invoking it.
- **One finding = one focused commit**, each with a regression test; the LLM is always mocked and
  the `claude` binary faked — no paid API or network call in any test.
- **Green before, green after.** Start from a green baseline; only commit passing code; end with a
  full deterministic green run.
- **Update the same review docs in place** — status + "Fixes applied" + "Architecture impact"; no
  new parallel documents.
- **Contracts stay recorded.** A seam change updates `spec/architecture.md` + its contract test in
  the same commit, so later reconciliation is accurate.
- **Docs before a release.** A patch that changes user-visible behavior updates `README.md`/`docs/`
  before the version is cut.
- **Release only with consent** (`--release` or an explicit confirmation) — and only as a `C` patch
  on an already-released phase.
- **Stop on failure.** A red `pytest`/`ruff` on any fix halts the sweep — report what landed and
  what remains; never paper over it.
