import uuid
from datetime import datetime
from .db import db


class Voter(db.Model):
    __tablename__ = "voters"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aadhaar_hash = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    epic_id = db.Column(db.String(10), unique=True, nullable=False)
    face_embedding = db.Column(db.Text, nullable=True)  # Face biometric template
    fingerprint_template = db.Column(db.Text, nullable=True)  # Raw fingerprint template for similarity matching
    fingerprint_hash = db.Column(db.String(64), nullable=True, unique=True)  # Fingerprint biometric
    fingerprint_fail_count = db.Column(db.Integer, nullable=False, default=0)
    fingerprint_locked = db.Column(db.Boolean, nullable=False, default=False)
    fp_dataset_id = db.Column(db.String(200), nullable=True)  # Deterministically assigned dataset fingerprint filename
    profile_data = db.Column(db.Text, nullable=True)  # Cached generated eKYC profile JSON
    has_voted = db.Column(db.Boolean, default=False)  # Prevent double voting
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Block(db.Model):
    __tablename__ = "blocks"

    id = db.Column(db.Integer, primary_key=True)
    previous_hash = db.Column(db.Text, nullable=False)
    data_hash = db.Column(db.Text, nullable=False)
    block_hash = db.Column(db.Text, nullable=False)
    hash_timestamp = db.Column(db.String(64), nullable=False)  # Timestamp used for hashing
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


class Biometric(db.Model):
    __tablename__ = "biometrics"

    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.UUID(as_uuid=True), nullable=False, index=True)
    face_embedding = db.Column(db.Text, nullable=False)
    liveness_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)
    party = db.Column(db.String(50), nullable=False)
    candidate_name = db.Column(db.String(100), nullable=False)
    constituency = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Vote(db.Model):
    __tablename__ = "votes"

    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.String(10), nullable=False, index=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    encrypted_vote = db.Column(db.Text, nullable=False)
    fingerprint_hash = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    block_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)