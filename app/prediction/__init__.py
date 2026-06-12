from flask import Blueprint

pred_bp = Blueprint('prediction', __name__)

from app.prediction import routes  # noqa: E402, F401
