from src.db import get_db


def make_lecturer_assignment(app, make_assignment):
    """make_assignment() creates its own lecturer; return (assignment_id, lecturer_id)."""
    assignment_id = make_assignment()
    with app.app_context():
        row = get_db().execute(
            'SELECT created_by FROM assignments WHERE id = ?', (assignment_id,)
        ).fetchone()
    return assignment_id, row['created_by']


# --- Step 1: create + list --------------------------------------------------

def test_lecturer_pages_redirect_to_login_when_logged_out(client):
    resp = client.get('/lecturer/assignments')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


def test_student_cannot_open_lecturer_pages(client, make_user, login_as):
    student_id, _ = make_user('student')
    login_as(student_id, 'student')
    assert client.get('/lecturer/assignments').status_code == 403
    assert client.get('/lecturer/assignments/new').status_code == 403


def test_lecturer_can_create_assignment(app, client, make_user, login_as):
    lecturer_id, _ = make_user('lecturer')
    login_as(lecturer_id, 'lecturer')
    resp = client.post('/lecturer/assignments/new', data={
        'title': 'Lab 3', 'description': 'Do the thing.',
        'deadline': '2026-12-01T10:00',
    })
    assert resp.status_code == 302
    with app.app_context():
        row = get_db().execute('SELECT * FROM assignments').fetchone()
    assert row['title'] == 'Lab 3'
    assert row['deadline'] == '2026-12-01T10:00'
    assert row['created_by'] == lecturer_id


def test_create_assignment_rejects_missing_fields_and_bad_deadline(
        app, client, make_user, login_as):
    lecturer_id, _ = make_user('lecturer')
    login_as(lecturer_id, 'lecturer')
    blank = client.post('/lecturer/assignments/new', data={
        'title': '', 'description': 'x', 'deadline': '2026-12-01T10:00'})
    bad_date = client.post('/lecturer/assignments/new', data={
        'title': 'T', 'description': 'x', 'deadline': 'next friday'})
    assert blank.status_code == 400
    assert bad_date.status_code == 400
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM assignments').fetchone()[0] == 0


def test_lecturer_only_sees_their_own_assignments(
        app, client, make_user, make_assignment, login_as):
    make_assignment(title='Someone elses')           # created by another lecturer
    me, _ = make_user('lecturer')
    login_as(me, 'lecturer')
    client.post('/lecturer/assignments/new', data={
        'title': 'Mine', 'description': 'x', 'deadline': '2026-12-01T10:00'})
    page = client.get('/lecturer/assignments').get_data(as_text=True)
    assert 'Mine' in page
    assert 'Someone elses' not in page


# --- Step 2: view submissions -----------------------------------------------

def add_submission(app, assignment_id, student_id, filename='work.pdf',
                   submitted_at='2026-01-01T09:00'):
    with app.app_context():
        db = get_db()
        cur = db.execute(
            'INSERT INTO submissions '
            '(assignment_id, student_id, filename, submitted_at) VALUES (?, ?, ?, ?)',
            (assignment_id, student_id, filename, submitted_at))
        db.commit()
        return cur.lastrowid


def test_lecturer_sees_submissions_with_late_flag(
        app, client, make_user, make_assignment, login_as):
    assignment_id, lecturer_id = make_lecturer_assignment(app, make_assignment)
    on_time, _ = make_user('student')
    late, _ = make_user('student')
    add_submission(app, assignment_id, on_time, 'ontime.pdf', '2000-01-01T09:00')
    add_submission(app, assignment_id, late, 'late.pdf', '2999-01-01T09:00')
    login_as(lecturer_id, 'lecturer')

    page = client.get(f'/lecturer/assignments/{assignment_id}/submissions')
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert 'ontime.pdf' in html and 'late.pdf' in html
    assert 'On time' in html and 'Late' in html


def test_lecturer_cannot_view_another_lecturers_submissions(
        app, client, make_user, make_assignment, login_as):
    assignment_id, _ = make_lecturer_assignment(app, make_assignment)
    other, _ = make_user('lecturer')
    login_as(other, 'lecturer')
    resp = client.get(f'/lecturer/assignments/{assignment_id}/submissions')
    assert resp.status_code == 404


# --- Step 3: download -------------------------------------------------------

def test_lecturer_can_download_submitted_file(
        app, client, make_user, make_assignment, login_as):
    assignment_id, lecturer_id = make_lecturer_assignment(app, make_assignment)
    student_id, _ = make_user('student')
    upload_dir = app.config['UPLOAD_FOLDER']
    import os
    os.makedirs(upload_dir, exist_ok=True)
    with open(os.path.join(upload_dir, 'essay.txt'), 'w') as f:
        f.write('hello lecturer')
    sub_id = add_submission(app, assignment_id, student_id, 'essay.txt')
    login_as(lecturer_id, 'lecturer')

    resp = client.get(f'/lecturer/submissions/{sub_id}/download')
    assert resp.status_code == 200
    assert resp.data == b'hello lecturer'
    assert 'attachment' in resp.headers['Content-Disposition']


def test_lecturer_cannot_download_another_lecturers_file(
        app, client, make_user, make_assignment, login_as):
    assignment_id, _ = make_lecturer_assignment(app, make_assignment)
    student_id, _ = make_user('student')
    sub_id = add_submission(app, assignment_id, student_id, 'essay.txt')
    other, _ = make_user('lecturer')
    login_as(other, 'lecturer')
    assert client.get(f'/lecturer/submissions/{sub_id}/download').status_code == 404
