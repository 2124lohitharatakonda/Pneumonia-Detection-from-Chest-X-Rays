"""
Upload utility helpers for the prediction blueprint.
"""
import os
import uuid
import logging

from flask import current_app
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Maximum allowed upload size: 5 MB
MAX_FILE_BYTES = 5 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    """
    Return True if the filename has an allowed extension.
    Extensions are sourced from app.config['ALLOWED_EXTENSIONS'].
    """
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'jpg', 'jpeg', 'png'})


def save_upload(file_storage) -> tuple:
    """
    Save an uploaded FileStorage object to the upload folder.

    Generates a UUID-based filename to prevent collisions and path-traversal attacks.

    Args:
        file_storage: werkzeug.datastructures.FileStorage from request.files

    Returns:
        (saved_filename: str, saved_path: str)

    Raises:
        ValueError: if the file or extension is invalid.
        OSError:    if the file cannot be written to disk.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError('No file was provided.')

    original = secure_filename(file_storage.filename)
    if not allowed_file(original):
        allowed = ', '.join(current_app.config.get('ALLOWED_EXTENSIONS', ['jpg', 'jpeg', 'png']))
        raise ValueError(f'Invalid file type. Allowed extensions: {allowed}')

    # Read file bytes to check size before writing
    file_bytes = file_storage.read()
    if len(file_bytes) == 0:
        raise ValueError('The uploaded file is empty.')
    if len(file_bytes) > MAX_FILE_BYTES:
        raise ValueError(
            f'File too large. Maximum allowed size is {MAX_FILE_BYTES // (1024 * 1024)} MB.'
        )

    ext = original.rsplit('.', 1)[1].lower()
    unique_name = f'{uuid.uuid4().hex}.{ext}'

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, unique_name)

    with open(save_path, 'wb') as fh:
        fh.write(file_bytes)

    logger.debug('Saved upload: %s', save_path)
    return unique_name, save_path
