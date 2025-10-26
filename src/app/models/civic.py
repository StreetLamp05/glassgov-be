import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Enum as PgEnum

from .. import db
from .enums import Category, VoteType



class CitizenPost(db.Model):
    __tablename__ = "citizen_posts"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(280), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(PgEnum(Category, name="category", create_type=True), nullable=False)
    city = db.Column(db.String(120), nullable=False)                 # normalization: city name (ex "Los Angeles"
    county = db.Column(db.String(120), nullable=True)                # ex "Los Angeles County"
    state_name = db.Column(db.String(50), db.ForeignKey("states.state_name"), nullable=False)
    score = db.Column(db.Integer, default=0)                         # upvotes/ downvotes
    created_at = db.Column(db.DateTime, default=datetime.now)

class PostVote(db.Model):
    __tablename__ = "post_votes"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(UUID(as_uuid=True), db.ForeignKey("citizen_posts.id", ondelete="CASCADE"), nullable=False)
    vote = db.Column(PgEnum(VoteType, name="vote_type", create_type=True), nullable=False)
    # MVP is anonymous. SO, store a server-side token hash to prevent double-voting from same browser
    voter_token_hash = db.Column(db.String(128), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    __table_args__ = (db.UniqueConstraint("post_id", "voter_token_hash", name="uq_post_vote_once_per_token"),)

class IssueTopicMatch(db.Model):
    __tablename__ = "issue_topic_matches"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(UUID(as_uuid=True), db.ForeignKey("citizen_posts.id", ondelete="CASCADE"), nullable=False)
    source_id = db.Column(UUID(as_uuid=True), db.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    score = db.Column(db.Float, nullable=False)                       # similarity 0...1 (tag overlap baseline)
    method = db.Column(db.String(32), nullable=False)                 # 'tag' (MVP) or 'embedding' (stretch)
    # TODO: NER EMBEDDING CHANGE HERE

class GeoContext(db.Model):
    __tablename__ = "geo_context"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city = db.Column(db.String(120), nullable=True)
    county = db.Column(db.String(120), nullable=True)
    state_name = db.Column(db.String(50), db.ForeignKey("states.state_name"), nullable=False)
    zipcode = db.Column(db.String(10), nullable=True)

    crime_index_12mo = db.Column(db.Numeric, nullable=True)          # >1 worse than baseline
    median_rent_usd = db.Column(db.Integer, nullable=True)
    median_income_usd = db.Column(db.Integer, nullable=True)
    population = db.Column(db.Integer, nullable=True)
    percent_poverty = db.Column(db.Numeric, nullable=True)
    as_of = db.Column(db.Date, nullable=True)