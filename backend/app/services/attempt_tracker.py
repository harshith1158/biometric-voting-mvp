"""
Attempt tracking and lockout enforcement.

Usage:
    from app.services.attempt_tracker import is_locked, record_failure, reset_attempts

After 3 consecutive failures for a (session_key, attempt_type) pair, the session
is locked for LOCKOUT_MINUTES minutes.  On success call reset_attempts() to clear.
"""
import logging
from datetime import datetime, timedelta

from app.db import db
from app.models import FailedAttempt

logger = logging.getLogger(__name__)

MAX_FAILURES = 3
LOCKOUT_MINUTES = 15


def is_locked(session_key: str, attempt_type: str) -> bool:
    """Return True if the session is currently locked out."""
    try:
        record = FailedAttempt.query.filter_by(
            session_key=session_key, attempt_type=attempt_type
        ).first()
        if not record or not record.locked_until:
            return False
        if record.locked_until > datetime.utcnow():
            return True
        # Lock expired — auto-clear
        record.fail_count = 0
        record.locked_until = None
        db.session.commit()
        return False
    except Exception as exc:
        logger.error("[ATTEMPT_TRACKER] is_locked error: %s", exc)
        return False


def get_lockout_remaining(session_key: str, attempt_type: str) -> int:
    """Return seconds remaining in lockout (0 if not locked)."""
    try:
        record = FailedAttempt.query.filter_by(
            session_key=session_key, attempt_type=attempt_type
        ).first()
        if not record or not record.locked_until:
            return 0
        delta = (record.locked_until - datetime.utcnow()).total_seconds()
        return max(0, int(delta))
    except Exception:
        return 0


def record_failure(session_key: str, attempt_type: str) -> dict:
    """
    Record one failed attempt.

    Returns dict:
        {'locked': bool, 'fail_count': int, 'remaining_attempts': int}
    """
    try:
        record = FailedAttempt.query.filter_by(
            session_key=session_key, attempt_type=attempt_type
        ).first()
        if record is None:
            record = FailedAttempt(
                session_key=session_key, attempt_type=attempt_type, fail_count=0
            )
            db.session.add(record)

        # If a previous lock has expired, reset the counter first
        if record.locked_until and record.locked_until <= datetime.utcnow():
            record.fail_count = 0
            record.locked_until = None

        record.fail_count += 1
        record.last_attempt = datetime.utcnow()

        if record.fail_count >= MAX_FAILURES:
            record.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            db.session.commit()
            logger.warning(
                "[ATTEMPT_TRACKER] '%s' locked for %s after %d failures",
                session_key[:16],
                attempt_type,
                record.fail_count,
            )
            return {"locked": True, "fail_count": record.fail_count, "remaining_attempts": 0}

        db.session.commit()
        remaining = MAX_FAILURES - record.fail_count
        return {
            "locked": False,
            "fail_count": record.fail_count,
            "remaining_attempts": remaining,
        }
    except Exception as exc:
        logger.error("[ATTEMPT_TRACKER] record_failure error: %s", exc)
        return {"locked": False, "fail_count": 0, "remaining_attempts": MAX_FAILURES}


def reset_attempts(session_key: str, attempt_type: str) -> None:
    """Reset attempt counter to 0 on successful verification."""
    try:
        record = FailedAttempt.query.filter_by(
            session_key=session_key, attempt_type=attempt_type
        ).first()
        if record:
            record.fail_count = 0
            record.locked_until = None
            db.session.commit()
    except Exception as exc:
        logger.error("[ATTEMPT_TRACKER] reset_attempts error: %s", exc)
