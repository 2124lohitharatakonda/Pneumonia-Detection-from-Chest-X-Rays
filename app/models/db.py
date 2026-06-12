"""
Database connection module.
Uses mysql-connector-python with a simple connection-per-request pattern
suitable for Flask's request lifecycle.
"""
import logging
import mysql.connector
from mysql.connector import Error as MySQLError
from flask import current_app, g

logger = logging.getLogger(__name__)


def get_db():
    """
    Return a database connection bound to the current Flask application context.
    Creates a new connection if one does not already exist for this request.
    """
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host=current_app.config['DB_HOST'],
                port=current_app.config['DB_PORT'],
                database=current_app.config['DB_NAME'],
                user=current_app.config['DB_USER'],
                password=current_app.config['DB_PASSWORD'],
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False,
                connection_timeout=10,
            )
        except MySQLError as exc:
            logger.error('Database connection failed: %s', exc)
            raise
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()


def init_app(app):
    """Register teardown handler with the Flask app."""
    app.teardown_appcontext(close_db)


# ── Helper wrappers ───────────────────────────────────────────────────────────

def execute_query(sql, params=None, fetch='all'):
    """
    Execute a SELECT query and return results.

    Args:
        sql:    SQL string with %s placeholders.
        params: Tuple or list of parameter values.
        fetch:  'all' → list of dicts; 'one' → single dict or None.

    Returns:
        List[dict] or dict or None.
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if fetch == 'one':
            return cursor.fetchone()
        return cursor.fetchall()
    except MySQLError as exc:
        logger.error('Query error [%s] params=%s error=%s', sql, params, exc)
        raise
    finally:
        cursor.close()


def execute_write(sql, params=None):
    """
    Execute an INSERT / UPDATE / DELETE statement.

    Returns:
        lastrowid (int) for INSERT, rowcount (int) for UPDATE/DELETE.
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(sql, params or ())
        db.commit()
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    except MySQLError as exc:
        db.rollback()
        logger.error('Write error [%s] params=%s error=%s', sql, params, exc)
        raise
    finally:
        cursor.close()
