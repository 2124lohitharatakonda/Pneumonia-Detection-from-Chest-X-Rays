"""
Flask extension instances.
Instantiated here (without app) and initialised in create_app().
"""
from flask_wtf.csrf import CSRFProtect
from flask_session import Session

csrf = CSRFProtect()
server_session = Session()
