import functools
import sqlite3

from flask import (Blueprint, flash, redirect, render_template, request,
                   session)
from werkzeug.security import check_password_hash, generate_password_hash

from src.db import get_db

bp = Blueprint('auth', __name__)


def login_required(role=None):
    """Protect a view. Pass role='student' or role='lecturer' to restrict it.

    Shared by every feature module, so keep this signature unchanged.
    """
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                return redirect('/login')
            if role and session.get('role') != role:
                flash('You do not have permission to view that page.')
                return redirect('/')
            return view(*args, **kwargs)
        return wrapped
    return decorator


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        reg_no = request.form.get('reg_no', '').strip()
        password = request.form.get('password', '')
        error = None
        if not (full_name and email and reg_no and password):
            error = 'All fields are required.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        if error is None:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO users (full_name, email, reg_no, password_hash, role) "
                    "VALUES (?, ?, ?, ?, 'student')",
                    (full_name, email, reg_no, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                error = 'That email or registration number is already registered.'
            else:
                flash('Registration successful. Please log in.')
                return redirect('/login')
        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = get_db().execute(
            'SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Incorrect email or password.')
        else:
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['full_name']
            return redirect('/')
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect('/login')