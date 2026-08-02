---
name: execute-issues
description: Execute GitHub issues for a phase sequentially - implement, validate, commit, push, and generate a report.
---

# Skill: Execute GitHub Issues

Execute GitHub issues for a phase sequentially: implement, validate, commit,
push, and generate a report.

## Usage

```
/execute-issues <label> [--phase vA.B] [--issue MC-xxx] [--dry-run]
```

The `<label>` is the GitHub version label exactly as it appears (e.g., `v0::version:0`).

- `/execute-issues v0::version:0 --phase v0.2` -- execute all open issues of phase v0.2
- `/execute-issues v0::version:0 --issue MC-010` -- execute a single issue
- `/execute-issues v0::version:0 --phase v0.2 --dry-run` -- show the execution plan without changes

**MyCom builds one phase per release (roadmap versioning model): execute the
issues of ONE phase, then stop.** Without `--phase`, ask the user which phase
to run rather than executing everything under the version label.

## Instructions

### Step 0: Verify prerequisites

1. Confirm we are on the expected branch (e.g., `main` or the user's working branch)
2. Confirm working tree is clean (`git status`)
3. Confirm `gh` is authenticated
4. Parse the label/phase: label `v0::version:0` + `--phase v0.2` → phase `v0.2`
5. Fetch issues from GitHub:
   ```bash
   gh issue list --label "{label}" --state open --limit 100
   ```
   and filter to the phase (the `Phase:` field in each issue body / the issues file).
6. Read the phase issues file for detailed descriptions: `spec/roadmap/implementation/v{A.B}-issues.md`
7. If a GitHub report exists (`spec/roadmap/implementation/v{A.B}-github-report.md`), read the MC-to-GitHub# mapping
8. Read [spec/roadmap.md](../../../spec/roadmap.md) for the phase Goal/Tasks/DoD
   (and the far-spec F-item acceptance criteria it references),
   [spec/architecture.md](../../../spec/architecture.md) for the components and
   invariants the issue must honor, and
   [spec/mission.md](../../../spec/mission.md) §Principles + §Non-goals
   (binding). `CLAUDE.md` (if present) has the code conventions.

### Step 1: Build execution queue

From the GitHub issue list, build an ordered queue based on dependencies:
- Parse MC-xxx IDs from issue titles (format: `MC-xxx: {title}`)
- Determine dependency order from the issues file dependency tree
- Issues with no unmet dependencies go first
- Skip issues already closed on GitHub
- If `--issue MC-xxx` is specified, execute only that issue (but verify its dependencies are closed)

Show the user the execution plan and ask for confirmation.

### Step 2: Execute each issue (loop)

For each issue in the queue:

#### 2a. Assign and announce

Print: `--- Starting MC-xxx: {title} ---`

#### 2b. Read issue details

Read the full issue description from the issues file (the detailed section for
this MC-xxx).

#### 2c. Implement

Execute the tasks described in the issue. Follow the conventions in `CLAUDE.md`
and the principles in `spec/mission.md`. Route by component and honor its
invariants ([spec/architecture.md](../../../spec/architecture.md)):

- **Panels / fs** (`mycom/panels/`, `mycom/fs/`): panels consume immutable
  `FileEntry` snapshots and never touch the disk directly; sorting stays a pure
  function; selection invariants (`..` unselectable, selection-else-cursor,
  deselect-on-success) hold.
- **File operations** (`mycom/fileops/`): plan → execute with injected
  policies; **no data loss** (source untouched until the operation completes;
  cancel safe at chunk boundaries); cross-device move = copy + verified delete.
- **Console** (`mycom/console/`): PTY passthrough (`script(1)` model); `cd`
  intercepted, never spawned; bounded ring buffer; cd-sync is an invariant.
- **Viewer / editor** (`mycom/viewer/`, `mycom/editor/`): windowed reads —
  never load a file whole; EOL and trailing-newline preservation; guards
  (dirty-close, external-change) always prompt.
- **Widgets / keymap / theme** (`mycom/widgets/`, `keymap.py`, `theme.py`):
  every modal is built on the dialog kit (zero ad-hoc modal code); no
  hard-coded keys or colors — keymap registry and theme files only.
- **AI** (`mycom/ai/`): everything goes through the `LLMClient` seam — the
  core never imports the Anthropic SDK directly; offline degradation (no AI
  object before first invocation); confirm-before-run for generated commands;
  structured outputs for programmatic results.
- **Claude Code** (`mycom/claude_code/`): binary discovery on PATH with a
  graceful missing-binary dialog; suspend/attach owns nothing of the child's
  terminal semantics; agent tool-use goes through TUI permission dialogs.
- **Platform** (`mycom/platform/`): the only place OS-conditional code lives.
- **Single-writer rule (global):** workers never touch widgets; anything
  > 100 ms runs async with visible progress.
- **Contract changes:** any change to a stable seam (FileEntry shape, selection
  invariants, plan/policy seams, keymap registry, theme format, `LLMClient`,
  state-DB schema) updates `spec/architecture.md` **AND** its contract test, in
  the same commit.
- Follow existing style/patterns; keep each phase self-contained (don't pull
  later phases' scope in early — mission Non-goals are binding).

#### 2d. Validate

Run validation checks (Python):

1. **Tests:** `pytest` (unit + contract tests pinning the seams + Pilot-driven
   integration tests — keyboard flows, not direct method calls).
2. **Lint:** `ruff check {changed paths}` (and `ruff format --check` if configured).
3. **Syntax/import:** `python3 -m py_compile {changed_py_files}` and an import check for changed modules.
4. **Contract consistency:** the touched seams match `spec/architecture.md` and their contract tests.
5. **Acceptance criteria:** go through each criterion from the issue and verify against the phase DoD in `spec/roadmap.md` (and the referenced far-spec F-items).

Record pass/fail for each check. **Tests are part of the work.** No paid or
networked calls in validation/CI: mock the `LLMClient` seam, fake the `claude`
binary; filesystem behavior runs on tmpfs fixtures, not mocks.

#### 2e. Commit

```bash
git add {specific files created/modified}
git commit -m "$(cat <<'EOF'
MC-xxx: {title}

{1-2 sentence summary of what was implemented}

Closes #{github-issue-number}

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

#### 2f. Push

```bash
git push
```

#### 2g. Close issue with summary

```bash
gh issue close {issue-number} --comment "$(cat <<'EOF'
## Implementation Summary

**Commit:** {commit-hash}
**Files changed:** {count}

### What was done
{bullet list of key changes}

### Validation
{pass/fail status for each check}

### Acceptance criteria
{checklist with pass/fail}
EOF
)"
```

#### 2h. Log progress

Append to the in-memory execution log: issue ID + title, commit hash, files
changed, validation results, status (success/partial/failed).

### Step 3: Handle failures

If implementation or validation fails for an issue:

1. Do NOT commit broken code
2. Revert changes: `git checkout -- .`
3. Add a comment to the GitHub issue explaining what failed
4. Log the failure
5. Ask the user: continue to next issue (if no dependency), or stop?

### Step 3b: Stop at the phase boundary; no auto-release

**When the phase's issues are all done, STOP.** Do not start the next phase —
the user reviews and launches it manually. **Do NOT bump the version
automatically.** Never change the version (VERSION file, RELEASE.txt, or git
tag) without explicit user confirmation; report completion and let the user
decide whether/when to release via `/release-version`.

Version notation `A.B.C`: `A` = roadmap version (v0→0), `B` = phase
(`v0.3`→B=3), `C` = post-release fix. Roadmap phase `vA.B` → semver `A.B.0`
(e.g. v0.3 → `0.3.0`). If some issues failed or were skipped, do NOT release —
note in the report that the phase is incomplete.

### Step 4: Generate execution report

After all issues are processed (or on stop), generate
`spec/roadmap/implementation/v{A.B}-execution-report.md`:

```markdown
# Phase v{A.B} -- Execution Report

**Date:** {date}
**Branch:** {branch name}
**Label:** {label}
**Target release:** {A.B.0}
**Executed by:** Claude Code

## Summary

| Status | Count |
|--------|-------|
| Completed | {n} |
| Failed | {n} |
| Skipped | {n} |
| Remaining | {n} |

## Issues

| # | MC ID | Title | Phase | Status | Commit | Files | Tests |
|---|-------|-------|-------|--------|--------|-------|-------|
| 1 | MC-009 | ... | v0.1 | completed | a1b2c3d | 4 | pass |

## Detailed Results

### MC-009: ...
**Status:** completed · **Commit:** a1b2c3d
**Validation:** [x] pytest · [x] ruff · [x] contracts · [x] acceptance

## Next Steps
{remaining issues + dependencies; or "phase complete — awaiting user review and /release-version A.B.0"}
```

Commit and push the report (`MC`-style message, with the Co-Authored-By
trailer).

## Important Rules

- **One issue at a time.** Never work on multiple issues simultaneously.
- **One phase at a time.** Execute only the given phase's issues; stop at the phase boundary — the user launches the next phase.
- **Dependency order.** Never start an issue whose dependencies are not closed.
- **Clean commits.** Each issue = one commit. No mixing work across issues.
- **No broken code.** Only commit code that passes validation (pytest + ruff).
- **Tests ship with the feature.** Mock the `LLMClient` seam and the `claude` binary; never call paid APIs or the network; drive UI acceptance through Pilot key presses.
- **Scope discipline.** Mission Non-goals are binding: no v2+ features early, no plugin system, AI stays optional (offline degradation), generated commands never auto-execute.
- **No data loss.** File operations never leave the source in a broken state; cancellation is always safe.
- **Contracts stay stable.** A seam change updates `spec/architecture.md` and its contract test in the same commit.
- **Ask on ambiguity.** If an issue description is unclear, ask the user rather than guessing.
- **Progress updates.** Print a short status line after each issue completes.
