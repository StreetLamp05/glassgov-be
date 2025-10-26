from flask import Blueprint, request, current_app
# stubs: wire OpenStates later
bp = Blueprint("refresh", __name__)

@bp.post("/openstates")
def refresh_openstates():
    # TODO: load LA city council items & insert into sources
    # For MVP, you can seed via script and return 200 here.
    return {"ok": True}
