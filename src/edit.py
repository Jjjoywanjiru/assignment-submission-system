"""Edit a submission before the deadline (Change Request CR-001).

A student can replace the file and/or change the comment of their own
submission while the assignment deadline has not passed. After the deadline
the submission is locked. Owner: Member D.
See docs/change-requests/CR-001-edit-submission.md.
"""
import os
import uuid

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)
from werkzeug.utils import secure_filename

from src.db import get_db, now_str
from src.student import allowed_file, is_late, student_required

bp = Blueprint('edit', __name__)


def get_own_submission(db, submission_id, student_id):
    """Return the submission only if it belongs to this student."""
    return db.execute(
        'SELECT s.*, a.title, a.deadline '
        'FROM submissions s '
        'JOIN assignments a ON a.id = s.assignment_id '
        'WHERE s.id = ? AND s.student_id = ?',
        (submission_id, student_id),
    ).fetchone()


@bp.route('/submissions/<int:submission_id>/edit', methods=['GET', 'POST'])
@student_required
def edit_submission(submission_id):
    db = get_db()
    submission = get_own_submission(db, submission_id, session['user_id'])
    if submission is None:
        # Missing or someone else's: do not reveal which.
        abort(404)

    # Deadline passed: show the page locked, with no form.
    if is_late(now_str(), submission['deadline']):
        return render_template('edit/edit_submission.html',
                               submission=submission, locked=True), 403

    if request.method == 'POST':
        file = request.files.get('file')
        comment = request.form.get('comment', '').strip()
        new_filename = submission['filename']
        replaced = False

        if file is not None and file.filename != '':
            if not allowed_file(file.filename):
                flash('That file type is not allowed.')
                return render_template('edit/edit_submission.html',
                                       submission=submission,
                                       locked=False), 400
            new_filename = (f'{submission["assignment_id"]}_'
                            f'{session["user_id"]}_{uuid.uuid4().hex[:8]}_'
                            f'{secure_filename(file.filename)}')
            upload_dir = current_app.config['UPLOAD_FOLDER']
            file.save(os.path.join(upload_dir, new_filename))
            replaced = True

        db.execute(
            'UPDATE submissions SET filename = ?, comment = ?, updated_at = ? '
            'WHERE id = ? AND student_id = ?',
            (new_filename, comment or None, now_str(),
             submission_id, session['user_id']),
        )
        db.commit()

        # Delete the old file only after the new one is saved and recorded.
        if replaced:
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    submission['filename'])
            if os.path.exists(old_path):
                os.remove(old_path)

        flash('Your submission was updated.')
        return redirect(url_for('student.my_submissions'))

    return render_template('edit/edit_submission.html',
                           submission=submission, locked=False)
