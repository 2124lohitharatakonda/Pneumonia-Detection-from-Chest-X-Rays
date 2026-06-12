"""
User model — data-access functions for the `users` table.
All queries use parameterized statements to prevent SQL injection.
"""
from .db import execute_query, execute_write


def create_user(name, email, password_hash, contact_number, verification_token=None):
    """
    Insert a new user row.

    Returns:
        int — the new user's id.
    """
    sql = """
        INSERT INTO users (name, email, password_hash, contact_number, verification_token)
        VALUES (%s, %s, %s, %s, %s)
    """
    return execute_write(sql, (name, email, password_hash, contact_number, verification_token))


def get_user_by_email(email):
    """
    Fetch a single user row by email address.

    Returns:
        dict or None.
    """
    sql = "SELECT * FROM users WHERE email = %s LIMIT 1"
    return execute_query(sql, (email,), fetch='one')


def get_user_by_id(user_id):
    """
    Fetch a single user row by primary key.

    Returns:
        dict or None.
    """
    sql = "SELECT * FROM users WHERE id = %s LIMIT 1"
    return execute_query(sql, (user_id,), fetch='one')


def get_user_by_token(token):
    """
    Fetch a user by their email-verification token.

    Returns:
        dict or None.
    """
    sql = "SELECT * FROM users WHERE verification_token = %s LIMIT 1"
    return execute_query(sql, (token,), fetch='one')


def verify_user_email(user_id):
    """Mark user as email-verified and clear the token."""
    sql = """
        UPDATE users
        SET email_verified = 1, verification_token = NULL
        WHERE id = %s
    """
    execute_write(sql, (user_id,))


def email_exists(email):
    """Return True if the email is already registered."""
    sql = "SELECT 1 FROM users WHERE email = %s LIMIT 1"
    result = execute_query(sql, (email,), fetch='one')
    return result is not None
