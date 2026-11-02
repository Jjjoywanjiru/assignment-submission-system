from datetime import datetime
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, send_from_directory, session,
                   url_for)

from src.db import get_db, now_str

bp = Blueprint('lecturer', __name__, url_prefix='/lecturer')

DEADLINE_FORMAT = '%Y-%m-%dT%H:%M'  # what <input type="datetime-local"> sends


def lecturer_required(view):
    """Only logged-in lecturers may use these pages.

    Not logged in -> send to /login. Logged in as a student -> 403.
    Uses the session keys Member A's login sets: user_id, role, name.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        if session.get('role') != 'lecturer':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# --- Step 1: create assignments and list them -------------------------------

@bp.route('/assignments')
@lecturer_required
def assignments():
    rows = get_db().execute(
        'SELECT a.*, COUNT(s.id) AS submission_count '
        'FROM assignments a '
        'LEFT JOIN submissions s ON s.assignment_id = a.id '
        'WHERE a.created_by = ? '
        'GROUP BY a.id '
        'ORDER BY a.deadline DESC',
        (session['user_id'],),
    ).fetchall()
    return render_template('lecturer/assignments.html', assignments=rows)


@bp.route('/assignments/new', methods=['GET', 'POST'])
@lecturer_required
def new_assignment():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        deadline = request.form.get('deadline', '').strip()

        error = None
        if not title or not description or not deadline:
            error = 'Title, description and deadline are all required.'
        else:
            try:
                datetime.strptime(deadline, DEADLINE_FORMAT)
            except ValueError:
                error = 'Deadline is not a valid date and time.'

        if error:
            flash(error)
            return render_template('lecturer/new_assignment.html',
                                   form=request.form), 400

        db = get_db()
        db.execute(
            'INSERT INTO assignments '
            '(title, description, deadline, created_by, created_at) '
            'VALUES (?, ?, ?, ?, ?)',
            (title, description, deadline, session['user_id'], now_str()),
        )
        db.commit()
        flash('Assignment created.')
        return redirect(url_for('lecturer.assignments'))

    return render_template('lecturer/new_assignment.html', form={})


# --- Step 2: view an assignment's submissions -------------------------------

def get_own_assignment(assignment_id):
    """Fetch an assignment, but only if the logged-in lecturer created it."""
    assignment = get_db().execute(
        'SELECT * FROM assignments WHERE id = ? AND created_by = ?',
        (assignment_id, session['user_id']),
    ).fetchone()
    if assignment is None:
        abort(404)
    return assignment


@bp.route('/assignments/<int:assignment_id>/submissions')
@lecturer_required
def submissions(assignment_id):
    assignment = get_own_assignment(assignment_id)
    rows = get_db().execute(
        'SELECT s.*, u.full_name, u.email, u.reg_no, '
        '       (s.submitted_at > a.deadline) AS is_late '
        'FROM submissions s '
        'JOIN users u ON u.id = s.student_id '
        'JOIN assignments a ON a.id = s.assignment_id '
        'WHERE s.assignment_id = ? '
        'ORDER BY s.submitted_at',
        (assignment_id,),
    ).fetchall()
    return render_template('lecturer/submissions.html',
                           assignment=assignment, submissions=rows)


# --- Step 3: download a submitted file --------------------------------------

@bp.route('/submissions/<int:submission_id>/download')
@lecturer_required
def download_submission(submission_id):
    row = get_db().execute(
        'SELECT s.filename FROM submissions s '
        'JOIN assignments a ON a.id = s.assignment_id '
        'WHERE s.id = ? AND a.created_by = ?',
        (submission_id, session['user_id']),
    ).fetchone()
    if row is None:
        abort(404)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               row['filename'], as_attachment=True)
