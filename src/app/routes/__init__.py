from flask import Blueprint
from .. import db


bp = Blueprint("routes", __name__)

'''
example route init:

from .user_routes import bp as user_bp

bp.register_blueprint(user_bp)
'''

@bp.get("/health")
def health():
    return {"ok": True}

