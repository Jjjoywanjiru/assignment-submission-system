# Requirements

**Project:** Student Assignment Submission System (USIU-Africa)
**Document status:** Configuration item, version controlled in Git.

## 1. Purpose

Allow students to submit assignments online and lecturers to create assignments
and review submissions.

## 2. Users

| User | Description |
| --- | --- |
| Student | Registers, views assignments, submits and tracks work |
| Lecturer | Creates assignments and reviews student submissions |

## 3. Functional requirements

| ID | Requirement | Release |
| --- | --- | --- |
| FR-1 | A student can register with name, email and password. | v1.0 |
| FR-2 | Students and lecturers can log in and log out. | v1.0 |
| FR-3 | Pages are restricted by role (student or lecturer). | v1.0 |
| FR-4 | A lecturer can create an assignment with a title, description and deadline. | v1.1 |
| FR-5 | A lecturer can view each student's submissions per assignment and download files. | v1.1 |
| FR-6 | A student can view the list of available assignments. | v1.2 |
| FR-7 | A student can submit a file for an assignment. | v1.2 |
| FR-8 | A student can view the status of their submissions, including late submissions. | v1.2 |
| FR-9 | A student can edit (replace) their submission before the deadline. | v1.3 (CR-001) |
| FR-10 | Edits are not allowed after the deadline. | v1.3 (CR-001) |
| FR-11 | A student can edit only their own submissions. | v1.3 (CR-001) |

## 4. Non-functional requirements

| ID | Requirement |
| --- | --- |
| NFR-1 | Passwords are stored hashed, never in plain text. |
| NFR-2 | Secrets (such as the secret key) are kept out of the repository. |
| NFR-3 | Uploaded files are limited to allowed types (pdf, doc, docx, txt, zip, py). |
| NFR-4 | The application runs locally with Python 3.12 and SQLite, with no separate database server. |
| NFR-5 | Every feature has automated pytest tests. |

## 5. Change history of this document

| Date | Change | Reference |
| --- | --- | --- |
| initial | FR-1 to FR-8 and NFRs documented | docs-feature branch |
| after v1.2 | FR-9 to FR-11 added | CR-001 |
