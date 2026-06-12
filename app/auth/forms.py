import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Regexp, ValidationError
)
from app.models.user import email_exists


class RegistrationForm(FlaskForm):
    name = StringField(
        'Full Name',
        validators=[
            DataRequired(message='Name is required.'),
            Length(min=2, max=100, message='Name must be between 2 and 100 characters.'),
            Regexp(
                r'^[A-Za-z\s\-\.]+$',
                message='Name may only contain letters, spaces, hyphens, and dots.'
            ),
        ],
    )
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.'),
            Length(max=255, message='Email too long.'),
        ],
    )
    contact_number = StringField(
        'Contact Number',
        validators=[
            DataRequired(message='Contact number is required.'),
            Regexp(
                r'^\+?[0-9\s\-\(\)]{7,20}$',
                message='Enter a valid contact number (7–20 digits, may include +, -, spaces, parentheses).'
            ),
        ],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, max=128, message='Password must be at least 8 characters.'),
        ],
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.'),
        ],
    )
    submit = SubmitField('Register')

    def validate_password(self, field):
        """Enforce password strength: at least one digit and one letter."""
        value = field.data
        if not re.search(r'[A-Za-z]', value):
            raise ValidationError('Password must contain at least one letter.')
        if not re.search(r'[0-9]', value):
            raise ValidationError('Password must contain at least one digit.')

    def validate_email(self, field):
        """Ensure email is not already registered."""
        if email_exists(field.data.strip().lower()):
            raise ValidationError('That email is already registered. Please log in.')


class LoginForm(FlaskForm):
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.'),
        ],
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
        ],
    )
    submit = SubmitField('Login')
