import uuid
from datetime import datetime
from .db import db


class Voter(db.Model):
    __tablename__ = "voters"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aadhaar_hash = db.Column(db.Text, nullable=False)
    phone_hash = db.Column(db.Text, nullable=False)
    epic_id = db.Column(db.Text, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Block(db.Model):
    __tablename__ = "blocks"

    id = db.Column(db.Integer, primary_key=True)
    previous_hash = db.Column(db.Text, nullable=False)
    data_hash = db.Column(db.Text, nullable=False)
    block_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OTPSession(db.Model):
    __tablename__ = "otp_sessions"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_hash = db.Column(db.Text, nullable=False, index=True)
    otp_hash = db.Column(db.Text, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_valid(self):
        return not self.is_used and self.expires_at > datetime.utcnow()