DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    reg_no TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'lecturer'))
);

CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    deadline TEXT NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users (id),
    created_at TEXT NOT NULL
);

CREATE TABLE submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL REFERENCES assignments (id),
    student_id INTEGER NOT NULL REFERENCES users (id),
    filename TEXT NOT NULL,
    comment TEXT,
    submitted_at TEXT NOT NULL,
    updated_at TEXT,
    status TEXT NOT NULL DEFAULT 'Submitted',
    UNIQUE (assignment_id, student_id)
);