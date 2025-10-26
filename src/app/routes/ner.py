from flask import Blueprint, request
from ..services.ner_service import analyze

bp = Blueprint("ner", __name__)

@bp.post("/analyze")
def run():
    data = request.get_json(force=True)
    text = data.get("text","")
    return analyze(text)
