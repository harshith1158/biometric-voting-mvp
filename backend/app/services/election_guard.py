"""
Election status guard.

Import is_election_open() in any endpoint that must be blocked after
the admin declares the result.

Usage:
    from app.services.election_guard import is_election_open

    if not is_election_open():
        return jsonify({"error": "Election is closed. This action is no longer permitted."}), 403
"""
import logging

from app.db import db
from app.models import ElectionStatus

logger = logging.getLogger(__name__)


def is_election_open() -> bool:
    """
    Return True if the election is still open.
    Returns True (fail-open) if the table is empty or an error occurs,
    to avoid blocking legitimate voters due to a DB glitch.
    """
    try:
        status = ElectionStatus.query.first()
        if not status:
            return True  # No status row yet → election open by default
        return status.status == "open"
    except Exception as exc:
        logger.error("[ELECTION_GUARD] Status check failed: %s", exc)
        return True  # Fail-open
