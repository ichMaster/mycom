---
name: upload-issues
description: Upload issues from a phase issues file to GitHub one by one with proper labels and dependencies.
---

# Skill: Upload Phase Issues to GitHub

Upload issues from a phase issues file to GitHub one by one, with proper labels and dependencies.

## Usage

```
/upload-issues <phase-number>
```

Example: `/upload-issues 1`

## Instructions

### Step 1: Read the phase issues file

Read the phase issues file at `spec/roadmap/phase-{N}-issues.md`.

Determine from the phase number:
- **x** (major): `0` (current major version)
- **y** (phase): from the argument (e.g., `1`)
- **Label prefix**: `phase:{y}` (e.g., `phase:1`)
- **Target release**: `0.{y}.0` (e.g., `0.1.0`)

Parse the **Issues Summary Table** to extract for each issue:
- `ID` (e.g., MC-001)
- `Title`
- `Size` (S, M, L)
- `Stage` (e.g., "1 — Scaffold")
- `Dependencies` (list of MC-xxx IDs)

Then parse each **detailed issue section** (## heading with MC-xxx) to extract:
- `Description`
- `What needs to be done` (full content)
- `Dependencies`
- `Expected result`
- `Acceptance criteria` (checklist)

### Step 2: Confirm with user

Show the user a summary of what will be created:
- Number of issues
- Label prefix (e.g., `phase:1`)
- Target release version (e.g., `0.1.0`)
- Full list of labels that will be created
- Ask for confirmation before proceeding

### Step 3: Create labels (if they don't exist)

Use `gh` to create these labels if they don't already exist:

```bash
# Phase label
gh label create "phase:1" --color "0052CC" --description "Phase 1 — Foundation" 2>/dev/null || true

# Size labels
gh label create "size:S" --color "28A745" --description "Small (1-2 days)" 2>/dev/null || true
gh label create "size:M" --color "FFC107" --description "Medium (3-5 days)" 2>/dev/null || true
gh label create "size:L" --color "DC3545" --description "Large (5-8 days)" 2>/dev/null || true

# Stage labels (extract from issues)
gh label create "stage:scaffold" --color "6F42C1" 2>/dev/null || true
# ... etc for each unique stage found in the issues
```

### Step 4: Create issues ONE BY ONE

**IMPORTANT:** Issues must be created one at a time, sequentially. After creating each issue:
1. Show the user the result (issue number, URL)
2. Proceed to the next issue immediately (do not wait for confirmation between issues)

For each issue (in order from the summary table):

1. Build the issue body in markdown:

```markdown
## Description
{description from the detailed section}

## What needs to be done
{full content from the detailed section}

## Dependencies
{dependency list, with references to already-created issue numbers}

## Expected result
{expected result from the detailed section}

## Acceptance criteria
{checklist from the detailed section}

---
**ID:** {MC-xxx}
**Size:** {S/M/L}
**Phase:** {y}
**Version:** 0.{y}.0
**Stage:** {stage name}
```

2. Create the issue:

```bash
gh issue create \
  --title "MC-xxx: {title}" \
  --label "phase:{y},size:{S/M/L},stage:{stage-name}" \
  --body "$(cat <<'BODY'
{issue body}
BODY
)"
```

3. Record the mapping: MC-xxx -> GitHub issue #number

4. Report to user: `Created MC-xxx → #{number}: {title}`

5. If the issue has dependencies on already-created issues, add a comment:

```bash
gh issue comment {issue-number} --body "Blocked by #{dep-issue-number} (MC-xxx)"
```

6. Move to the next issue.

### Step 5: Generate report

After all issues are created, generate a report file at:
`spec/roadmap/phase-{N}-github-report.md`

Content:

```markdown
# Phase {N} — GitHub Issues Report

**Uploaded:** {date}
**Repository:** {github repo URL}
**Target version:** 0.{N}.0
**Total issues:** {count}

## Issue Mapping

| MC ID | GitHub # | Title | Labels | URL |
|-------|----------|-------|--------|-----|
| MC-001 | #1 | Project scaffold and package structure | phase:1, size:S, stage:scaffold | {url} |
| ... | ... | ... | ... | ... |

## Labels Created

- phase:{N}
- size:S, size:M, size:L
- stage:{list}
```

Commit and push the report:

```bash
git add spec/roadmap/phase-{N}-github-report.md
git commit -m "$(cat <<'EOF'
Add Phase {N} GitHub issues report

Uploaded {count} issues to GitHub with labels and dependencies.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
git push
```

### Step 6: Report to user

Show the user:
- Total issues created
- Link to the GitHub issues list
- Path to the generated report file

## Version Scheme

Version format: `x.y.z` where x=major (0), y=phase, z=fix.

- Phase 1 issues → labels prefixed with `phase:1`
- Phase 2 issues → labels prefixed with `phase:2`
- Phase 3 issues → labels prefixed with `phase:3`

## Error Handling

- If `gh` is not authenticated, tell the user to run `gh auth login`
- If an issue already exists with the same title, skip it and note in the report
- If label creation fails, continue (labels may already exist)
- On any failure, report what was created so far and what remains
