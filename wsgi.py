"""
Production WSGI entry point.

Windows:
    waitress-serve --port=5000 wsgi:app

Linux/Mac:
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app('production')
