import os

import click
from flask import Flask, redirect, session
from werkzeug.security import generate_password_hash

from src.db import close_db, get_db, init_db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-change-me'),
        DATABASE=os.path.join(app.root_path, 'database', 'app.db'),
        UPLOAD_FOLDER=os.path.join(app.root_path, 'uploads'),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.teardown_appcontext(close_db)

    from src import auth, edit, lecturer, student
    app.register_blueprint(auth.bp)
    app.register_blueprint(lecturer.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(edit.bp)

    @app.route('/')
    def index():
        role = session.get('role')
        if role == 'student':
            return redirect('/assignments')
        if role == 'lecturer':
            return redirect('/lecturer/assignments')
        return redirect('/login')

    @app.cli.command('init-db')
    def init_db_command():
        """Create the database tables from database/schema.sql."""
        init_db()
        click.echo('Database initialised.')

    @app.cli.command('create-lecturer')
    @click.argument('email')
    @click.argument('password')
    @click.option('--name', default='Lecturer')
    def create_lecturer_command(email, password, name):
        """Create a lecturer account (lecturers cannot self-register)."""
        db = get_db()
        db.execute(
            "INSERT INTO users (full_name, email, password_hash, role) "
            "VALUES (?, ?, ?, 'lecturer')",
            (name, email.lower(), generate_password_hash(password)),
        )
        db.commit()
        click.echo('Lecturer created.')

    return app


app = create_app()