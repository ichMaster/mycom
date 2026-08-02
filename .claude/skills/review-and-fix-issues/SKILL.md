---
name: review-and-fix-issues
description: Code-review a released phase or the current branch, write a criticality-ranked recommendations doc in spec/roadmap/implementation/, implement the fix-now items with regression tests, then record what was done in the SAME doc. Never releases.
---

# Skill: Review & Fix Issues

Run one loop over the codebase: **review → recommend → fix → record.** It (1) performs a critical
code review, (2) writes a single recommendations document ranking findings by criticality and marking
each **FIX NOW** or **DEFER →**, (3) implements the fix-now items with regression tests, and (4)
**updates that same document in place** — marking what was fixed and adding a "Fixes applied"
section. The recommendations and the results live in **one document**.

This skill fixes only the small, in-scope, high-value findings. It **never** bumps the version or
cuts a release (that stays `/release-version`, explicit), and it never pulls deferred/larger work
forward without flagging it.

## Usage

```
/review-and-fix-issues [target]
```

- `/review-and-fix-issues v0.4` — review the phase v0.4 work (through its release tag if released).
- `/review-and-fix-issues` — review the **current branch / working tree** (everything built so far).
- `/review-and-fix-issues fileops` — scope the review to one component (`panels`/`fs`/`fileops`/
  `console`/`viewer`/`editor`/`widgets`/`ai`/`claude-code`/`state`/`platform`).

## Instructions

### Step 0: Scope + green baseline

1. Resolve `target`: a phase (`vA.B`), a version (`vA`), a component name, or — with no argument —
   the **current branch** (the whole codebase).
2. Confirm we are on the working branch and the tree is clean.
3. **Establish a green baseline** — run `pytest` + `ruff check`. If the suite is **red or flaky**,
   say so: a review on a red baseline is unreliable. Fix a clear flake first (small, focused, its own
   commit) or surface it and ask before continuing. **Never review or fix on top of a red suite.**

### Step 1: Critical code review

Read the in-scope modules — route by [spec/architecture.md](../../../spec/architecture.md)
§Components — and focus on the highest-risk seams first: the file-operations engine (no-data-loss,
conflict/recovery policies, cancellation), the console/PTY runner (passthrough, `cd` interception,
ring buffer bounds), the selection model, the state DB (migrations, corruption recovery), and the
AI layer (`LLMClient` seam, offline rule, confirm-before-run).

Be **adversarial** — hunt for *real* defects, not restatements of what works:
- **Data loss:** any path where a failed or cancelled operation can corrupt or lose source files;
  cross-device move deleting before the copy is verified; conflict "All" answers leaking across
  operations.
- **Single-writer violations:** workers or callbacks mutating widgets directly; blocking calls
  (> 100 ms scans, sync IO) on the event loop; cancellation via thread kill instead of flags.
- **Correctness:** selection invariants (`..` selectable? selection surviving a directory change?),
  sort stability, EOL/trailing-newline round-trips, cursor-restore rules, keymap contexts.
- **Robustness:** EACCES/ENOENT mid-operation, broken symlinks, a vanished panel path, a corrupt
  state DB, a command printing 100k lines, malformed PTY output.
- **AI discipline:** any core import of the Anthropic SDK outside the `LLMClient` seam; an AI object
  constructed before first invocation (breaks the offline rule); a generated command path that can
  execute without explicit Run; danger patterns missing from the classifier.
- **Input hygiene & secrets:** `ANTHROPIC_API_KEY` reaching logs, config files, or prompts; shell
  quoting of file names (spaces, quotes, newlines) in generated or constructed commands; path
  traversal in archive/extract paths.
- **Seam drift:** code that diverges from the pinned contracts in `spec/architecture.md` or pulls
  v2+ scope in early (mission Non-goals).

For each finding, capture: a **concrete failure scenario** (inputs → wrong result/crash), a
`file:line` anchor, a **severity** (🔴 HIGH / 🟠 MEDIUM / 🟡 LOW), and a **proposed fix**. Cross-check
findings against the specs; if a gap is *already scheduled* for a later phase (e.g. v1.3 error
recovery, v1.2 auto-refresh), note that rather than treating it as new.

### Step 2: Write the recommendations document (the plan)

Write **one** doc at `spec/roadmap/implementation/<scope>-code-review.md` (e.g.
`v0.4-code-review.md`, or `branch-code-review.md` for the working tree). Include:

- A header: date, reviewer, **scope**, method.
- A **criticality-ranked summary table** with columns: `# | Severity | Finding | Recommendation |
  Status`. **Recommendation** is `FIX NOW` or `DEFER → <home>`; **Status** starts as blank/pending.
- Per-finding detail: the failure scenario + the proposed fix.
- A short **"What's solid"** section (keep the review balanced).
- **Suggested next actions.**

Decide **FIX NOW vs DEFER** honestly:
- **FIX NOW** = real, small, self-contained, high-value, and in-scope now (e.g. a data-loss path,
  a single-writer violation, trivial input validation).
- **DEFER →** = larger resilience work, or anything already owned by a later roadmap phase — give
  the home (`v1.3`, `v1.5`, "cleanup/`/simplify`", "documented MVP scope"). Do **not** pull these
  forward.

Commit the doc as the plan (a `docs:` commit).

### Step 3: Implement the FIX-NOW items (with tests)

For each **FIX NOW** finding, in criticality order:

1. Implement the fix following `CLAUDE.md` + `spec/architecture.md`. Keep it minimal and in-scope.
2. **Add a regression test that would have caught the bug** (a data-loss finding gets a
   cancelled-mid-tree tmpfs test, a keymap finding gets a Pilot key-press test, …). The **LLM is
   always mocked** (the `LLMClient` seam) and the `claude` binary is faked — no paid or networked
   call in any test.
3. **Validate:** `pytest` (green, deterministic) + `ruff check`. Only commit code that passes.
4. **Commit** one focused change per finding, referencing the finding number
   (`fix(<area>): … (code review #N)`), with the `Co-Authored-By` trailer.
5. **Seam changes** (FileEntry shape, selection invariants, plan/policy seams, keymap registry,
   theme format, `LLMClient`, state-DB schema) update `spec/architecture.md` **and** the contract
   test in the **same** commit.

If a fix turns out larger than "fix now" (touches a seam broadly, or needs design), **stop,
re-classify it to DEFER** in the doc with the reason, and move on — don't half-land it.

### Step 4: Update the SAME document (the result)

Edit the doc **in place**:
- Flip the **Status** column to `✅ FIXED — <commit>` for each applied fix (and keep `⏳ deferred`
  for the rest).
- Add a **"Fixes applied"** section: per fix, the change, the regression test, and the verification
  (final `pytest` + `ruff` status). For any fix that **changed a documented contract or a
  design-relevant behavior**, add an explicit **"Architecture impact"** note (what changed vs the
  original design), and ensure `spec/architecture.md` reflects contract changes. This record is what
  a later `/generate-issues` reconciles the next phase against — so the next phase builds on what
  was really implemented, not the stale design.
- Update **"Suggested next actions"** (e.g. `/release-version` for a patch on a released phase;
  carry deferred items into their phase).

Commit the doc update (a `docs:` commit).

### Step 5: Report

Summarize: findings by severity; which were **fixed** (with commits) and which **deferred** (with
homes); the final green suite + lint status. If fixes landed on an already-released phase, suggest
`/release-version A.B.C` (the `C` patch) — but do **not** run it. Offer a deeper adversarial pass
(`/code-review ultra`) for confirmation.

## Important Rules

- **One document, updated in place.** The recommendations and the results share a single doc — mark
  what was fixed and add the "Fixes applied" section rather than writing a new file.
- **Fix only the fix-now items.** Never pull deferred or larger work forward without re-classifying
  and explaining it in the doc.
- **Every fix ships a regression test**, the LLM is always mocked and the `claude` binary faked —
  no paid API or network call in any test.
- **Green before, green after.** Establish a green baseline; only commit code that passes `pytest`
  + `ruff`; keep the suite deterministic.
- **Record architecture deltas.** A seam/contract change updates `spec/architecture.md` and its
  contract test in the **same** commit. Any fix that alters documented behavior gets an
  **"Architecture impact"** note in the review doc — so the next `/generate-issues` can reconcile
  the following phase against what was really built, not the stale design.
- **Never release.** No version bump, no tag — recommend `/release-version` and stop.
- **Ask on genuine ambiguity** — an unclear scope, or a borderline finding where fix-now vs defer
  is a real judgment call the user should make.
