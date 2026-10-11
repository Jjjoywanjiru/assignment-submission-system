from datetime import datetime
from pathlib import Path
import sqlite3

from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    schema = Path(current_app.root_path) / 'database' / 'schema.sql'
    db = get_db()
    db.executescript(schema.read_text())
    db.commit()


def now_str():
    return datetime.now().isoformat(timespec='minutes')