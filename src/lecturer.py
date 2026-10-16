from datetime import datetime
from functools import wraps

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)

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
