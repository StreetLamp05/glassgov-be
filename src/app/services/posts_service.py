from .. import db
from ..models.civic import CitizenPost, PostVote, IssueTopicMatch
from ..models.enums import VoteType, Category
from .ner_service import analyze

def create_post(title: str, body: str, city: str, county: str | None, state_name: str):
    ner = analyze(f"{title}\n{body}")
    primary = Category(ner["category"])
    post = CitizenPost(title=title, body=body, category=category, city=city, county=county, state_name=state_name)
    db.session.add(post)
    db.session.flush()  # get post.id

    # baseline tag-overlap matcher stub: match after topics exist; for now empty
    return post

def list_posts(city: str | None, state_name: str | None, category: str | None, limit: int = 20):
    q = CitizenPost.query
    if city: q = q.filter(CitizenPost.city.ilike(city))
    if state_name: q = q.filter(CitizenPost.state_name == state_name)
    if category: q = q.filter(CitizenPost.category == Category(category))
    return q.order_by(CitizenPost.score.desc(), CitizenPost.created_at.desc()).limit(limit).all()

def vote_post(post_id, voter_token_hash: str | None, vote: VoteType):
    # enforce once-per-token
    if voter_token_hash:
        existing = PostVote.query.filter_by(post_id=post_id, voter_token_hash=voter_token_hash).first()
        if existing:
            # if same vote, ignore; if opposite, flip score by 2
            if existing.vote == vote:
                return
            delta = 2 if vote == VoteType.up else -2
            existing.vote = vote
        else:
            db.session.add(PostVote(post_id=post_id, voter_token_hash=voter_token_hash, vote=vote))
            delta = 1 if vote == VoteType.up else -1
    else:
        # anonymous with no token: still allow, but no dedupe (dev-only)
        db.session.add(PostVote(post_id=post_id, vote=vote))
        delta = 1 if vote == VoteType.up else -1

    post = CitizenPost.query.get(post_id)
    post.score = (post.score or 0) + delta
    db.session.commit()
    return post
