"""
Auth utilities: email sending, token generation, login guard.
"""
import secrets
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

from flask import session, redirect, url_for, flash, current_app

logger = logging.getLogger(__name__)


def generate_token(nbytes=32):
    """Return a cryptographically secure URL-safe token string."""
    return secrets.token_urlsafe(nbytes)


def login_required(f):
    """
    Decorator that redirects unauthenticated users to the login page.
    Usage:
        @login_required
        def my_view():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def send_verification_email(recipient_email, recipient_name, token):
    """
    Send an HTML email with an email-verification link.

    Args:
        recipient_email: str
        recipient_name:  str
        token:           str — the verification token stored in the DB

    Returns:
        True on success, False on failure (never raises).
    """
    try:
        verify_url = url_for('auth.verify_email', token=token, _external=True)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Verify Your Email — Pneumonia Detection System'
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = recipient_email

        html_body = f"""
        <html><body>
        <h2>Hello, {recipient_name}!</h2>
        <p>Thank you for registering with the <strong>Pneumonia Detection System</strong>.</p>
        <p>Please verify your email address by clicking the button below:</p>
        <p>
            <a href="{verify_url}"
               style="background:#007bff;color:#fff;padding:10px 20px;
                      text-decoration:none;border-radius:4px;display:inline-block;">
                Verify Email
            </a>
        </p>
        <p>Or copy this link into your browser:<br>
           <small>{verify_url}</small>
        </p>
        <p>If you did not register, please ignore this email.</p>
        <br><p>— The Pneumonia Detection System Team</p>
        </body></html>
        """

        text_body = (
            f"Hello {recipient_name},\n\n"
            f"Verify your email by visiting:\n{verify_url}\n\n"
            "If you did not register, ignore this email."
        )

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(
            current_app.config['MAIL_SERVER'],
            current_app.config['MAIL_PORT'],
        ) as server:
            server.ehlo()
            if current_app.config['MAIL_USE_TLS']:
                server.starttls()
            server.login(
                current_app.config['MAIL_USERNAME'],
                current_app.config['MAIL_PASSWORD'],
            )
            server.sendmail(
                current_app.config['MAIL_DEFAULT_SENDER'],
                recipient_email,
                msg.as_string(),
            )
        logger.info('Verification email sent to %s', recipient_email)
        return True

    except Exception as exc:
        logger.error('Failed to send email to %s: %s', recipient_email, exc)
        return False
