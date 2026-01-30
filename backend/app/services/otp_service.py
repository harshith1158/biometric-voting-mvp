import hashlib
import secrets
from datetime import datetime, timedelta
from app.models import OTPSession
from app.db import db


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_otp() -> str:
    return str(secrets.randbelow(1000000)).zfill(6)


def create_otp_session(phone: str) -> tuple[str, str]:
    """Generate OTP and create session. Returns (otp, hashed_otp)"""
    otp = generate_otp()
    otp_hash = hash_value(otp)
    phone_hash = hash_value(phone)
    expires_at = datetime.utcnow() + timedelta(minutes=2)

    session = OTPSession(
        phone_hash=phone_hash,
        otp_hash=otp_hash,
        expires_at=expires_at,
    )
    db.session.add(session)
    db.session.commit()

    return otp, otp_hash


def verify_otp(phone: str, otp: str) -> bool:
    """Verify OTP and mark as used if valid"""
    phone_hash = hash_value(phone)
    otp_hash = hash_value(otp)

    session = OTPSession.query.filter_by(
        phone_hash=phone_hash,
        otp_hash=otp_hash,
    ).order_by(OTPSession.created_at.desc()).first()

    if not session:
        return False

    if not session.is_valid():
        return False

    session.is_used = True
    db.session.commit()
    return True


def cleanup_expired_otps():
    """Delete expired OTP sessions"""
    OTPSession.query.filter(
        OTPSession.expires_at <= datetime.utcnow()
    ).delete()
    db.session.commit()
