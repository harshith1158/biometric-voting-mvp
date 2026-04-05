import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from app.models import OTPSession
from app.db import db

logger = logging.getLogger(__name__)


def hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_otp() -> str:
    return str(secrets.randbelow(1000000)).zfill(6)


def create_otp_session(phone: str) -> tuple[str, str]:
    """Generate OTP and create session. Returns (otp, hashed_otp)"""
    otp = generate_otp()
    otp_hash = hash_value(otp)
    phone_hash = hash_value(phone)
    # Increased from 2 minutes to 10 minutes (industry standard)
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    session = OTPSession(
        phone_hash=phone_hash,
        otp_hash=otp_hash,
        expires_at=expires_at,
    )
    db.session.add(session)
    db.session.commit()

    logger.info(f"OTP created for phone_hash: {phone_hash[:8]}... expires at {expires_at}")
    return otp, otp_hash


def verify_otp(phone: str, otp: str) -> tuple[bool, str]:
    """
    Verify OTP and mark as used if valid.
    
    Args:
        phone: Phone number
        otp: OTP to verify
    
    Returns:
        tuple: (success, message)
    """
    phone_hash = hash_value(phone)
    otp_hash = hash_value(otp)

    # Find most recent OTP session for this phone
    session = OTPSession.query.filter_by(
        phone_hash=phone_hash,
        otp_hash=otp_hash,
    ).order_by(OTPSession.created_at.desc()).first()

    if not session:
        logger.warning(f"OTP verification failed: No matching session for phone_hash")
        return False, "Invalid OTP"

    # Check if expired
    if session.expires_at <= datetime.utcnow():
        logger.warning(f"OTP verification failed: OTP expired")
        return False, "OTP has expired"

    # Check if already used (prevent replay attacks)
    if session.is_used:
        logger.warning(f"OTP verification failed: OTP already used (replay attack prevention)")
        return False, "OTP already used"

    # Mark as used (atomically update and commit)
    session.is_used = True
    db.session.commit()

    logger.info(f"OTP verification successful for phone_hash: {phone_hash[:8]}...")
    return True, "OTP verified successfully"


def cleanup_expired_otps():
    """Delete expired OTP sessions"""
    deleted = OTPSession.query.filter(
        OTPSession.expires_at <= datetime.utcnow()
    ).delete()
    db.session.commit()
    if deleted > 0:
        logger.info(f"Cleaned up {deleted} expired OTP sessions")
    return deleted
