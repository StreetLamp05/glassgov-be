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


from .posts import bp as posts_bp
from .topics import bp as topics_bp
from .context import bp as context_bp
from .refresh import bp as refresh_bp
from .openstates import bp as openstates_bp
from .ner import bp as ner_bp
from .discover import bp as discover_bp

bp.register_blueprint(posts_bp, url_prefix="/posts")
bp.register_blueprint(topics_bp, url_prefix="/topics")
bp.register_blueprint(context_bp, url_prefix="/context")
bp.register_blueprint(refresh_bp, url_prefix="/refresh")
bp.register_blueprint(openstates_bp, url_prefix="/openstates")
bp.register_blueprint(ner_bp, url_prefix="/ner")
bp.register_blueprint(discover_bp, url_prefix="/discover")
