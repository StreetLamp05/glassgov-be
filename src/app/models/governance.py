import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy import Enum as PgEnum

from .. import db
from .enums import JurisdictionLevel, Branch, BodyType, SourceType

class Jurisdiction(db.Model):
    __tablename__ = 'jurisdictions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(120), nullable=False)  # e.g. "City of Los Angeles"
    level = db.Column(PgEnum(JurisdictionLevel, name="jurisdiction_level", create_type=True), nullable=False)
    state_name = db.Column(db.String(50), db.ForeignKey("states.state_name"), nullable=False)  # fk to states table

    created_at = db.Column(db.DateTime, default=datetime.now)

class Body(db.Model):
    __tablename__ = "bodies"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction_id = db.Column(UUID(as_uuid=True), db.ForeignKey("jurisdictions.id"), nullable=False)
    name = db.Column(db.String(160), nullable=False)  # "Los Angeles City Council"
    branch = db.Column(PgEnum(Branch, name="branch", create_type=True), nullable=False)
    body_type = db.Column(PgEnum(BodyType, name="body_type", create_type=True), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=True)

class District(db.Model):
    __tablename__ = "districts"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body_id = db.Column(UUID(as_uuid=True), db.ForeignKey("bodies.id"), nullable=False)
    name = db.Column(db.String(80), nullable=True)                   # ex. "District 5"
    code = db.Column(db.String(40), nullable=True)                   # ex. "CD5"


class Official(db.Model):
    __tablename__ = "officials"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body_id = db.Column(UUID(as_uuid=True), db.ForeignKey("bodies.id"), nullable=False)
    district_id = db.Column(UUID(as_uuid=True), db.ForeignKey("districts.id"), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    email = db.Column(db.String(160), nullable=True)
    next_meeting = db.Column(db.DateTime, nullable=True)

class Source(db.Model):
    __tablename__ = "sources"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body_id = db.Column(UUID(as_uuid=True), db.ForeignKey("bodies.id"), nullable=True)
    source_type = db.Column(PgEnum(SourceType, name="source_type", create_type=True), nullable=True)
    external_id = db.Column(db.String(120), nullable=True)           # council file number, bill id,.. etc
    title = db.Column(db.String(400), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(80), nullable=True)
    meeting_datetime = db.Column(db.DateTime, nullable=True)
    url = db.Column(db.String(600), nullable=True)
    tags = db.Column(ARRAY(db.String), default=[])
    raw = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("body_id", "source_type", "external_id", name="uq_source_body_type_ext"),
    )

class Meeting(db.Model):
    __tablename__ = "meetings"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body_id = db.Column(UUID(as_uuid=True), db.ForeignKey("bodies.id"), nullable=False)
    meeting_datetime = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    agenda_source_id = db.Column(UUID(as_uuid=True), db.ForeignKey("sources.id"), nullable=True)


class AgendaItem(db.Model):
    __tablename__ = "agenda_items"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = db.Column(UUID(as_uuid=True), db.ForeignKey("meetings.id"), nullable=False)
    item_number = db.Column(db.String(40), nullable=True)   # "Item 4"
    title = db.Column(db.String(400), nullable=True)
    description = db.Column(db.Text, nullable=True)
    related_source_id = db.Column(UUID(as_uuid=True), db.ForeignKey("sources.id"), nullable=True)
    tags = db.Column(ARRAY(db.String), default=[])