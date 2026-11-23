# Recovery Report: reverting a faulty change (CR-002)

This report records a deliberate faulty change, how it was detected, and how
it was reversed, to show how the team recovers from a bad change.

| Field | Detail |
| --- | --- |
| Change request | CR-002: "tidy" the deadline check on the edit page |
| Branch | `faulty-change` (created from `main`) |
| Raised by | Member D |
| Result | Fault detected by tests and reversed with `git revert` |
| Release | v1.3.1 (code identical to v1.3 plus the Edit button) |

## 1. The faulty change

Commit: *Tidy deadline check in edit page (CR-002, DEMO: contains a deliberate
fault)*. One line in `src/edit.py`: the arguments to `is_late()` were swapped.

```diff
-    if is_late(now_str(), submission['deadline']):
+    if is_late(submission['deadline'], now_str()):
```

`is_late(a, b)` is true when `a` is after `b`. With the arguments swapped, the
edit page is **locked before the deadline** and **open after it**, which is the
opposite of requirements FR-9 and FR-10.

## 2. Detection

`pytest` failed straight away:

```
FAILED tests/test_edit.py::test_edit_page_loads_before_deadline
FAILED tests/test_edit.py::test_replace_file_before_deadline
FAILED tests/test_edit.py::test_comment_only_edit_keeps_file
FAILED tests/test_edit.py::test_edit_blocked_after_deadline
FAILED tests/test_edit.py::test_rejects_disallowed_file_type
5 failed, 28 passed
```

The test names point directly at the edit deadline rule, so the cause was
found in minutes. Without tests, students would have been blocked from editing
in time and able to change work after the deadline.

## 3. Containment

The change lived only on the `faulty-change` branch and was reviewed in a pull
request, so it never became the working version on `main` without the revert
that undoes it. If a faulty change is ever merged, the same steps below apply
on `main`, and the team is told straight away not to build on top of it.

## 4. Recovery

Use `git revert`. It adds a new commit that undoes the bad one, so history is
kept and teammates who already pulled are not affected.

```bash
git log --oneline          # find the faulty commit
git revert HEAD            # or: git revert <commit-id>
pytest                     # confirm everything passes again
git push
```

Resulting history on the branch (newest first):

```
Add change request and recovery records, changelog
Revert "Tidy deadline check in edit page (CR-002)"
Tidy deadline check in edit page (CR-002, DEMO: contains a deliberate fault)
```

## 5. Verification

- `src/edit.py` is identical to `main` again (`git diff origin/main -- src`
  shows nothing).
- `pytest`: all tests pass.

## 6. Why revert and not reset

| | `git revert` | `git reset --hard` and force push |
| --- | --- | --- |
| History | Kept, with a clear "undo" entry | Bad commit disappears |
| Teammates who already pulled | Not affected | Their copies conflict with the remote |
| Evidence for this report | Yes | No |
| Safe on a shared branch | Yes | No |

Use `git reset` only on commits that exist on your own computer and have never
been pushed.

## 7. Lessons learned

1. A "tidy-up" that should not change behaviour still needs the test suite.
2. Tests that check both sides of a rule (before and after the deadline) are
   what caught this fault.
3. Small single-purpose commits make a revert clean: this fault was one line.
4. Merge this branch with a normal merge, not a squash, so the fault and its
   revert stay visible in history.
