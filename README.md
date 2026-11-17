# Student Assignment Submission System

A simple web application for USIU-Africa where students submit assignments and
lecturers manage them. Built for **SFE 4015 Software Configuration Management
(Assignment 2)** to demonstrate how SCM is applied across a project.

## Features

**Students:** register and log in, view available assignments, submit a file,
view submission status, and edit a submission before the deadline (CR-001).

**Lecturers:** log in, create assignments with a deadline, and view and
download student submissions.

## Tech stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.12 |
| Web framework | Flask |
| Database | SQLite |
| Frontend | HTML, CSS, Bootstrap, Jinja2 |
| Passwords | Werkzeug password hashing |
| File storage | Local `uploads/` folder |
| Testing | pytest |
| Version control | Git and GitHub (Issues, Pull Requests, Branches, Tags, Releases) |

## Getting started

```bash
git clone <repository-url>
cd <repository-folder>

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit the values in .env
sqlite3 database/app.db < database/schema.sql
# existing databases: also run each file in database/migrations/ once, in order

flask --app app run             # open http://127.0.0.1:5000
```

Never commit `.env`, the database file, or the `uploads/` folder. They are
listed in `.gitignore`.

## Running the tests

```bash
pytest
```

All tests must pass before a pull request is merged.

## Project structure

```
app.py                  Flask application entry point
src/                    One blueprint per feature
  auth.py               Registration, login, logout (Member A)
  lecturer.py           Lecturer features (Member B)
  student.py            Student features (Member C)
  edit.py               Edit submission, CR-001 (Member D)
templates/              Jinja2 templates, one folder per feature
database/
  schema.sql            Database tables (tracked as code)
  migrations/           Numbered schema changes
tests/                  pytest tests, one file per feature
docs/                   Requirements, user guide, change requests, recovery report
```

## Team and responsibilities

| Member | Responsibility | Branch | Release |
| --- | --- | --- | --- |
| A | Repository setup, registration and login | `login-feature` | v1.0 |
| B | Lecturer features | `lecturer-feature` | v1.1 |
| C | Student features | `submission-feature` | v1.2 |
| D | Documentation, change request, recovery demo | `docs-feature`, `edit-submission`, `faulty-change` | v1.3, v1.3.1 |

## Branching strategy

- `main` is always the stable, working version. **Nobody commits directly to `main`.**
- Each feature is developed on its own branch created from `main`.
- When a feature is ready, open a **pull request** into `main`. One teammate
  reviews it, and the tests must pass before merging.
- After merging, the release owner tags the new version on `main`.

## Commit messages

Write a short sentence that says what changed. Good: `Added student login
functionality`. Not acceptable: `changes`, `updated`, `fix`.
Commits that implement the change request mention it, e.g. `(CR-001)`.

Before your first commit, set your real identity so the history shows who did
what:

```bash
git config user.name "Your Name"
git config user.email "your-github-email@example.com"
```

## Change management

Changes after the first release go through a change request:

1. Record the request as a GitHub Issue (template: `docs/change-requests/`).
2. Create a branch for the change.
3. Implement it and write tests.
4. Open a pull request that links the Issue; a teammate reviews it.
5. Merge to `main`, tag a new version, and update `CHANGELOG.md`.

Records: [`CR-001`](docs/change-requests/CR-001-edit-submission.md) (edit a
submission before the deadline) and the
[recovery report](docs/recovery-report.md) (reverting a faulty change).

## Releases

See [`CHANGELOG.md`](CHANGELOG.md) and the GitHub Releases page.

## Documentation

- [Requirements](docs/requirements.md)
- [User guide](docs/user-guide.md)
