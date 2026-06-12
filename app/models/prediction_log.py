"""
Prediction log model — data-access functions for `prediction_logs` table.
"""
from .db import execute_query, execute_write


def create_log(user_id, image_filename, image_path, result,
               confidence_score, model_used, precaution_text=None):
    """
    Insert a new prediction log entry.

    Returns:
        int — the new log id.
    """
    sql = """
        INSERT INTO prediction_logs
            (user_id, image_filename, image_path, result,
             confidence_score, model_used, precaution_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    return execute_write(sql, (
        user_id, image_filename, image_path, result,
        confidence_score, model_used, precaution_text,
    ))


def get_logs_for_user(user_id, limit=20):
    """
    Return the most recent prediction logs for a given user.

    Returns:
        list[dict]
    """
    sql = """
        SELECT * FROM prediction_logs
        WHERE user_id = %s
        ORDER BY predicted_at DESC
        LIMIT %s
    """
    return execute_query(sql, (user_id, limit), fetch='all')


def get_log_by_id(log_id):
    """
    Return a single prediction log entry.

    Returns:
        dict or None.
    """
    sql = "SELECT * FROM prediction_logs WHERE id = %s LIMIT 1"
    return execute_query(sql, (log_id,), fetch='one')
