import os
import uuid
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from werkzeug.utils import secure_filename

from src.db import get_db, now_str

bp = Blueprint('student', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'zip', 'ppt', 'pptx',
                      'xls', 'xlsx', 'py', 'java', 'c', 'cpp', 'png', 'jpg',
                      'jpeg'}


def student_required(view):
    """Only logged-in students may use these pages.

    Not logged in -> send to /login. Logged in as a lecturer -> 403.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        if session.get('role') != 'student':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_late(submitted_at, deadline):
    """Both values are ISO strings 'YYYY-MM-DDTHH:MM', so string compare works."""
    return submitted_at > deadline


# --- Step 1: list available assignments -------------------------------------

@bp.route('/assignments')
@student_required
def assignments():
    rows = get_db().execute(
        'SELECT a.*, u.full_name AS lecturer_name, '
        '       s.id AS submission_id, s.submitted_at, s.status '
        'FROM assignments a '
        'JOIN users u ON u.id = a.created_by '
        'LEFT JOIN submissions s '
        '       ON s.assignment_id = a.id AND s.student_id = ? '
        'ORDER BY a.deadline',
        (session['user_id'],),
    ).fetchall()
    return render_template('student/assignments.html',
                           assignments=rows, now=now_str())


# --- Step 2: upload work ----------------------------------------------------

@bp.route('/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
@student_required
def submit(assignment_id):
    db = get_db()
    assignment = db.execute(
        'SELECT * FROM assignments WHERE id = ?', (assignment_id,)
    ).fetchone()
    if assignment is None:
        abort(404)

    existing = db.execute(
        'SELECT id FROM submissions WHERE assignment_id = ? AND student_id = ?',
        (assignment_id, session['user_id']),
    ).fetchone()
    if existing:
        flash('You have already submitted this assignment.')
        return redirect(url_for('student.my_submissions'))

    if request.method == 'POST':
        file = request.files.get('file')
        comment = request.form.get('comment', '').strip()

        error = None
        if file is None or file.filename == '':
            error = 'Please choose a file to upload.'
        elif not allowed_file(file.filename):
            error = 'That file type is not allowed.'

        if error:
            flash(error)
            return render_template('student/submit.html',
                                   assignment=assignment, now=now_str()), 400

        # Prefix keeps names unique so students never overwrite each other.
        stored_name = (f'{assignment_id}_{session["user_id"]}_'
                       f'{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}')
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name))

        submitted_at = now_str()
        status = 'Late' if is_late(submitted_at, assignment['deadline']) \
            else 'Submitted'
        db.execute(
            'INSERT INTO submissions '
            '(assignment_id, student_id, filename, comment, submitted_at, status) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (assignment_id, session['user_id'], stored_name, comment or None,
             submitted_at, status),
        )
        db.commit()
        if status == 'Late':
            flash('Submission received, but it was after the deadline (late).')
        else:
            flash('Submission received on time.')
        return redirect(url_for('student.my_submissions'))

    return render_template('student/submit.html',
                           assignment=assignment, now=now_str())


# --- Step 3: view own submission status -------------------------------------

@bp.route('/my-submissions')
@student_required
def my_submissions():
    rows = get_db().execute(
        'SELECT s.*, a.title, a.deadline, '
        '       (s.submitted_at > a.deadline) AS is_late '
        'FROM submissions s '
        'JOIN assignments a ON a.id = s.assignment_id '
        'WHERE s.student_id = ? '
        'ORDER BY s.submitted_at DESC',
        (session['user_id'],),
    ).fetchall()
    return render_template('student/my_submissions.html',
                           submissions=rows, now=now_str())