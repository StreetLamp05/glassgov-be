from flask import Blueprint, request
from ..services.posts_service import create_post, list_posts, vote_post
from ..models.enums import VoteType
from ..models.civic import CitizenPost

bp = Blueprint("posts", __name__)

@bp.post("/")
def create():
    data = request.get_json(force=True)
    post = create_post(
        title=data["title"],
        body=data["body"],
        city=data["city"],
        county=data.get("county"),
        state_name=data["state_name"],
    )
    return {
        "id": str(post.id),
        "title": post.title,
        "body": post.body,
        "category": post.category.value,
        "city": post.city,
        "state_name": post.state_name,
        "score": post.score,
        "created_at": post.created_at.isoformat(),
    }, 201

@bp.get("/")
def list_():
    city = request.args.get("city")
    state = request.args.get("state_name")
    category = request.args.get("category")
    posts = list_posts(city, state, category)
    return [{
        "id": str(p.id),
        "title": p.title,
        "body": p.body[:400],
        "category": p.category.value,
        "city": p.city,
        "state_name": p.state_name,
        "score": p.score,
        "created_at": p.created_at.isoformat(),
    } for p in posts]

@bp.post("/vote")
def vote():
    data = request.get_json(force=True)
    post_id = data["post_id"]
    vt = VoteType(data["vote"])
    token_hash = data.get("voter_token_hash")
    post = vote_post(post_id, token_hash, vt)
    return {"id": str(post.id), "score": post.score}
