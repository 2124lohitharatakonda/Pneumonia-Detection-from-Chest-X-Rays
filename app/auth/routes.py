import logging

from flask import render_template, redirect, url_for, flash, session, request
from werkzeug.security import generate_password_hash, check_password_hash

from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm
from app.auth.utils import generate_token, send_verification_email
from app.models.user import (
    create_user, get_user_by_email, get_user_by_id,
    get_user_by_token, verify_user_email,
)

logger = logging.getLogger(__name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if 'user_id' in session:
        return redirect(url_for('prediction.user_home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        name = form.name.data.strip()
        email = form.email.data.strip().lower()
        contact = form.contact_number.data.strip()
        password_hash = generate_password_hash(
            form.password.data, method='pbkdf2:sha256', salt_length=16
        )
        token = generate_token()

        try:
            user_id = create_user(name, email, password_hash, contact, token)
            logger.info('New user registered: id=%s email=%s', user_id, email)

            # Attempt to send verification email — non-blocking on failure
            sent = send_verification_email(email, name, token)
            if sent:
                flash(
                    'Registration successful! Please check your email to verify your account.',
                    'success',
                )
            else:
                # Still allow login even if email send failed
                flash(
                    'Registration successful! (Email verification skipped — '
                    'SMTP not configured.) You may log in now.',
                    'success',
                )

            return redirect(url_for('auth.login'))

        except Exception as exc:
            logger.error('Registration error: %s', exc)
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('auth/register.html', form=form, title='Register')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if 'user_id' in session:
        return redirect(url_for('prediction.user_home'))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data

        user = get_user_by_email(email)

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('Your account has been deactivated. Contact support.', 'danger')
                return render_template('auth/login.html', form=form, title='Login')

            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']

            logger.info('User logged in: id=%s email=%s', user['id'], email)
            flash(f"Welcome back, {user['name']}!", 'success')

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('prediction.user_home'))

        flash('Invalid email or password. Please try again.', 'danger')
        logger.warning('Failed login attempt for email=%s', email)

    return render_template('auth/login.html', form=form, title='Login')


@auth_bp.route('/logout')
def logout():
    """Clear the session and redirect to home."""
    name = session.get('user_name', 'User')
    session.clear()
    flash(f'You have been logged out. Goodbye, {name}!', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify a user's email address via token link."""
    user = get_user_by_token(token)
    if not user:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('auth.login'))

    if user['email_verified']:
        flash('Your email is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    verify_user_email(user['id'])
    flash('Email verified successfully! You may now log in.', 'success')
    return redirect(url_for('auth.login'))
