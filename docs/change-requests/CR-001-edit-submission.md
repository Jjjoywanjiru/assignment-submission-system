# CR-001: Edit a submission before the deadline

| Field | Detail |
| --- | --- |
| Status | Implemented (release v1.3) |
| Raised by | Member D |
| Type | New feature, low risk |
| Branches | `edit-submission` (route and tests), `edit-link` (Edit button) |
| Requirements | FR-9, FR-10, FR-11 in [requirements.md](../requirements.md) |
| Approver | ______________________ (Joy Wanjiru) |

## Why

After submitting, a student could not fix a wrong file or a mistake in the
comment. A second upload is blocked ("You have already submitted this
assignment"), so the only option was to ask the lecturer for help.

## What changes

- New page `/submissions/<id>/edit` (`src/edit.py`,
  `templates/edit/edit_submission.html`).
- An **Edit** button on *My submissions*, shown only while the deadline is
  open (`edit-link` branch).
- No database change: `submissions.updated_at` already exists in the schema.

## Rules

1. Only the student who made the submission can edit it. Anyone else gets 404.
2. Editing is allowed until the deadline. After it, the page is locked (403).
3. The student can replace the file, change the comment, or both.
4. The original `submitted_at` time is kept, so an on-time submission cannot
   become late by being edited. `updated_at` records the last edit.
5. The same allowed file types as the original upload apply. A replaced file
   is deleted from `uploads/` after the new one is saved.

## Risks and controls

| Risk | Control |
| --- | --- |
| Edit after the deadline | Deadline check on open and save, tested in `tests/test_edit.py` |
| Editing another student's work | Query filters on `student_id`, tested |
| Disallowed file types | Reuses `allowed_file()`, tested |
| Edit button shown when it should not be | `tests/test_edit_link.py` |
| Faulty change to the deadline check | See [recovery report](../recovery-report.md) |

## Verification

`pytest`: all tests pass, including `tests/test_edit.py` and
`tests/test_edit_link.py`.

## Rollback plan

Each part is its own commit or pull request, so it can be removed with
`git revert`. No data migration is needed.
