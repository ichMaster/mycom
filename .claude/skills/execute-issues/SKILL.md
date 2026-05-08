---
name: execute-issues
description: Execute GitHub issues for a phase sequentially - implement, validate, commit, push, and generate a report.
---

# Skill: Execute GitHub Issues

Execute GitHub issues for a phase sequentially: implement, validate, commit, push, and generate a report.

## Usage

```
/execute-issues <phase> [--issue MC-xxx] [--dry-run]
```

- `/execute-issues 1` — execute all issues for Phase 1
- `/execute-issues 1 --issue MC-003` — execute a single issue from Phase 1
- `/execute-issues 1 --dry-run` — show execution plan without making changes

## Instructions

### Step 0: Verify prerequisites

1. Confirm we are on the `main` branch (or the user's working branch)
2. Confirm working tree is clean (`git status`)
3. Confirm `gh` CLI is authenticated (`gh auth status`)
4. Parse the phase number to determine version target:
   - Phase `1` → target release `0.1.0`
   - Phase `N` → target release `0.N.0`
5. Fetch issues from GitHub:
   ```bash
   gh issue list --label "phase:1" --state open --limit 100
   ```
6. Read the phase issues file: `spec/roadmap/phase-{N}-issues.md`
7. Read the phase tasks file: `spec/roadmap/phase-{N}-tasks.md`
8. If an execution report exists (`phase-{N}-execution-report.md`), read the MC-to-GitHub# mapping

### Step 1: Build execution queue

From the GitHub issue list, build an ordered queue based on dependencies:
- Parse MC-xxx IDs from issue titles (format: `MC-xxx: {title}`)
- Determine dependency order from the phase issues file dependency tree
- Issues with no unmet dependencies go first
- Skip issues already closed on GitHub
- If `--issue MC-xxx` is specified, execute only that issue (but verify its dependencies are closed)

Show the user the execution plan and ask for confirmation.

### Step 2: Execute each issue (loop)

For each issue in the queue:

#### 2a. Assign and announce

```bash
gh issue edit {issue-number} --add-assignee "@me"
```

Print: `--- Starting MC-xxx: {title} ---`

#### 2b. Read issue details

Read the full issue description from the phase issues file (the detailed section for this MC-xxx). Also read all related tasks from the phase tasks file (tasks referencing this MC-xxx in the Issue column).

#### 2c. Implement

Execute the tasks described in the issue. Follow the architecture in `spec/architecture.md`. Key rules:

- Create files in the locations specified by the architecture's project structure
- Implement according to the issue description and acceptance criteria
- Follow existing code style and patterns from already-implemented modules
- Write tests alongside implementation when the issue includes test tasks

#### 2d. Validate

Run validation checks:

1. **Syntax check:** `python -m py_compile {changed_files}` for each new/modified .py file
2. **Import check:** `python -c "import {module}"` for each new module
3. **Tests:** `python -m pytest tests/ -x --tb=short` if tests exist
4. **Acceptance criteria:** go through each criterion from the issue and verify

Record pass/fail for each check.

#### 2e. Commit

```bash
git add {specific files created/modified}
git commit -m "$(cat <<'EOF'
MC-xxx: {title}

{1-2 sentence summary of what was implemented}

Closes #{github-issue-number}

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
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

Append to the in-memory execution log:
- Issue ID, title
- Commit hash
- Files changed (list)
- Validation results
- Status: success/partial/failed

### Step 3: Handle failures

If implementation or validation fails for an issue:

1. Do NOT commit broken code
2. Stash or revert changes: `git checkout -- .`
3. Add a comment to the GitHub issue explaining what failed
4. Log the failure
5. Ask the user: continue to next issue (if no dependency), or stop?

### Step 3b: Version bump on phase completion

After ALL issues in the phase are completed successfully (none failed, none remaining):

1. Determine the target version: Phase N → `0.N.0`

2. Update `VERSION` file:
   ```
   0.N.0
   ```

3. Update `mycom/__init__.py`:
   ```python
   __version__ = "0.N.0"
   ```

4. Update `pyproject.toml` version field

5. Update `RELEASE.txt` — replace the unreleased entry with dated entry and list all features:
   ```
   Version 0.N.0 (YYYY-MM-DD)
   ---------------------------
   - MC-xxx: {title} — {1-sentence summary}
   - MC-xxx: {title} — {1-sentence summary}
   ...
   ```

6. Commit the version bump:
   ```bash
   git add VERSION mycom/__init__.py pyproject.toml RELEASE.txt
   git commit -m "$(cat <<'EOF'
   Release v0.N.0 — Phase N complete

   All {count} issues implemented and validated.

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   EOF
   )"
   ```

7. Tag the release:
   ```bash
   git tag -a v0.N.0 -m "Phase N: {phase milestone name}"
   ```

8. Report: `Phase N complete → version bumped to 0.N.0, tagged v0.N.0`

If some issues failed or were skipped, do NOT bump the version.

### Step 4: Generate execution report

After all issues are processed (or on stop), generate:
`spec/roadmap/phase-{N}-execution-report.md`

```markdown
# Phase {N} — Execution Report

**Date:** {date}
**Branch:** {branch name}
**Target version:** 0.{N}.0
**Executed by:** Claude Code

## Summary

| Status | Count |
|--------|-------|
| Completed | {n} |
| Failed | {n} |
| Skipped | {n} |
| Remaining | {n} |

## Issues

| # | MC ID | Title | Status | Commit | Files | Tests |
|---|-------|-------|--------|--------|-------|-------|
| 1 | MC-001 | Project scaffold and package structure | completed | a1b2c3d | 15 | 0/0 |
| ... | ... | ... | ... | ... | ... | ... |

## Detailed Results

### MC-001: Project scaffold and package structure

**Status:** completed
**Commit:** a1b2c3d
**Files changed:**
- `mycom/__init__.py` (new)
- `pyproject.toml` (new)
- ...

**Validation:**
- [x] Syntax check: all files pass
- [x] Import check: all modules import
- [ ] Tests: N/A
- [x] Acceptance criteria: 5/5 pass

---

## Next Steps

{List of remaining issues not yet executed, with their dependencies}
```

Commit and push the report:

```bash
git add spec/roadmap/phase-{N}-execution-report.md
git commit -m "$(cat <<'EOF'
Add Phase {N} execution report

{n} issues completed, {n} failed, {n} remaining.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
git push
```

## Important Rules

- **One issue at a time.** Never work on multiple issues simultaneously.
- **Dependency order.** Never start an issue whose dependencies are not closed.
- **Clean commits.** Each issue = one commit. No mixing work across issues.
- **No broken code.** Only commit code that passes validation.
- **Version bump on phase completion.** When all issues in a phase pass, bump to `0.N.0` and tag.
- **Ask on ambiguity.** If an issue description is unclear, ask the user rather than guessing.
- **Progress updates.** Print a short status line after each issue completes.
