from flask import render_template, session
from app.main import main_bp


@main_bp.route('/')
def index():
    return render_template('index.html', title='Home')


@main_bp.route('/about')
def about():
    return render_template('about.html', title='About')
