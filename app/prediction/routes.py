import logging
import os

from flask import (
    render_template, redirect, url_for, flash,
    session, request, current_app,
)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField

from app.prediction import pred_bp
from app.prediction.predictor import predict
from app.prediction.utils import save_upload
from app.models.prediction_log import create_log, get_logs_for_user
from app.auth.utils import login_required

logger = logging.getLogger(__name__)


class UploadForm(FlaskForm):
    """WTF form for image upload — provides CSRF token and file validation."""
    image = FileField(
        'Chest X-Ray Image',
        validators=[
            FileRequired(message='Please select an image file.'),
            FileAllowed(
                ['jpg', 'jpeg', 'png'],
                message='Only JPEG and PNG images are allowed.'
            ),
        ],
    )
    model_choice = SelectField(
        'Detection Model',
        choices=[
            ('resnet50', 'DenseNet121 (91.8% Accuracy)'),
        ],
        default='resnet50',
    )
    submit = SubmitField('Analyze X-Ray')


@pred_bp.route('/user', methods=['GET'])
@login_required
def user_home():
    """User home page — show upload form and recent history."""
    form = UploadForm()
    user_id = session['user_id']
    history = []
    try:
        history = get_logs_for_user(user_id, limit=10)
    except Exception as exc:
        logger.warning('Could not fetch prediction history for user %s: %s', user_id, exc)

    return render_template(
        'prediction/user_home.html',
        form=form,
        history=history,
        title='Upload X-Ray',
    )


@pred_bp.route('/predict', methods=['POST'])
@login_required
def predict_image():
    """
    Handle X-ray image upload and run ML inference.

    Flow:
    1. Validate CSRF token (via Flask-WTF)
    2. Validate and save uploaded file
    3. Run model inference
    4. Log result to DB
    5. Render result page
    """
    form = UploadForm()

    if not form.validate_on_submit():
        # Re-render upload page with validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
        return redirect(url_for('prediction.user_home'))

    file_storage = request.files.get('image')
    model_choice = form.model_choice.data

    # ── 1. Save file ──────────────────────────────────────────────────────────
    try:
        filename, filepath = save_upload(file_storage)
    except ValueError as exc:
        flash(str(exc), 'danger')
        return redirect(url_for('prediction.user_home'))
    except OSError as exc:
        logger.error('File save error: %s', exc)
        flash('Could not save the uploaded file. Please try again.', 'danger')
        return redirect(url_for('prediction.user_home'))

    # ── 2. Run inference ──────────────────────────────────────────────────────
    try:
        result = predict(
            image_path=filepath,
            model_name=model_choice,
            model_dir=current_app.config['MODEL_DIR'],
        )
    except FileNotFoundError as exc:
        logger.error('Model not found: %s', exc)
        flash(
            'The selected model is not available. Please train it first or choose another.',
            'danger',
        )
        return redirect(url_for('prediction.user_home'))
    except Exception as exc:
        logger.error('Prediction error for file %s: %s', filepath, exc, exc_info=True)
        import traceback; traceback.print_exc()
        flash('An error occurred during analysis. Please try again.', 'danger')
        return redirect(url_for('prediction.user_home'))

    # ── 3. Log to database ────────────────────────────────────────────────────
    user_id = session['user_id']
    image_url = url_for('static', filename=f'uploads/{filename}')

    try:
        log_id = create_log(
            user_id=user_id,
            image_filename=filename,
            image_path=image_url,
            result=result['result'],
            confidence_score=result['confidence'],
            model_used=result['model_used'],
            precaution_text=result['precaution_text'],
        )
        logger.info(
            'Prediction logged: log_id=%s user_id=%s result=%s confidence=%.4f model=%s',
            log_id, user_id, result['result'], result['confidence'], result['model_used'],
        )
    except Exception as exc:
        # Log DB failure but don't block the user from seeing their result
        logger.error('Failed to log prediction to DB: %s', exc)

    # ── 4. Render result page ─────────────────────────────────────────────────
    return render_template(
        'prediction/result.html',
        image_url=image_url,
        result=result['result'],
        confidence=result['confidence'],
        confidence_pct=f"{result['confidence'] * 100:.1f}",
        model_used=result['model_used'],
        precaution_text=result['precaution_text'],
        raw_scores=result['raw_scores'],
        title='Prediction Result',
    )


@pred_bp.route('/history')
@login_required
def history():
    """View full prediction history for the current user."""
    user_id = session['user_id']
    try:
        logs = get_logs_for_user(user_id, limit=50)
    except Exception as exc:
        logger.error('History fetch error for user %s: %s', user_id, exc)
        flash('Could not load prediction history.', 'danger')
        logs = []

    return render_template(
        'prediction/history.html',
        logs=logs,
        title='My History',
    )
