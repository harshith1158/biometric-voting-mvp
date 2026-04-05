"""
Biometric deduplication service to prevent vote fraud.
Prevents same person from registering/voting multiple times using different Aadhaar.
"""

import hashlib
import numpy as np
from app.models import Voter
from app.db import db


def hash_fingerprint(fingerprint_data: bytes) -> str:
    """Hash fingerprint data for comparison."""
    return hashlib.sha256(fingerprint_data).hexdigest()


def similarity_score(embedding1: list, embedding2: list) -> float:
    """
    Calculate cosine similarity between two face embeddings.
    Returns value between 0 and 1 (1 = identical, 0 = completely different).
    """
    try:
        arr1 = np.array(embedding1, dtype=np.float32)
        arr2 = np.array(embedding2, dtype=np.float32)
        
        # Cosine similarity
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0


def check_duplicate_face(face_embedding: list, exclude_voter_id: str = None) -> dict:
    """
    Check if face embedding already exists in system (except exclude_voter_id).
    
    Returns:
        {
            "is_duplicate": bool,
            "matched_voter_id": str or None,
            "similarity": float,
            "threshold": 0.85
        }
    """
    FACE_SIMILARITY_THRESHOLD = 0.85  # 85% match = same person
    
    try:
        query = Voter.query.filter(Voter.face_embedding.isnot(None))
        if exclude_voter_id:
            query = query.filter(Voter.id != exclude_voter_id)
        
        existing_voters = query.all()
        
        for voter in existing_voters:
            embedded_data = eval(voter.face_embedding)  # Convert string to list
            similarity = similarity_score(face_embedding, embedded_data)
            
            if similarity >= FACE_SIMILARITY_THRESHOLD:
                return {
                    "is_duplicate": True,
                    "matched_voter_id": str(voter.id),
                    "similarity": similarity,
                    "threshold": FACE_SIMILARITY_THRESHOLD
                }
        
        return {
            "is_duplicate": False,
            "matched_voter_id": None,
            "similarity": 0.0,
            "threshold": FACE_SIMILARITY_THRESHOLD
        }
    except Exception as e:
        print(f"Error checking duplicate face: {e}")
        return {
            "is_duplicate": False,
            "matched_voter_id": None,
            "similarity": 0.0,
            "error": str(e)
        }


def check_duplicate_fingerprint(fingerprint_hash: str, exclude_voter_id: str = None) -> dict:
    """
    Check if fingerprint already exists (EXACT match only).
    
    Returns:
        {
            "is_duplicate": bool,
            "matched_voter_id": str or None
        }
    """
    try:
        query = Voter.query.filter(Voter.fingerprint_hash == fingerprint_hash)
        if exclude_voter_id:
            query = query.filter(Voter.id != exclude_voter_id)
        
        voter = query.first()
        
        if voter:
            return {
                "is_duplicate": True,
                "matched_voter_id": str(voter.id)
            }
        
        return {
            "is_duplicate": False,
            "matched_voter_id": None
        }
    except Exception as e:
        print(f"Error checking duplicate fingerprint: {e}")
        return {
            "is_duplicate": False,
            "error": str(e)
        }


def enroll_biometrics(voter_id: str, face_embedding: list = None, fingerprint_hash: str = None) -> bool:
    """
    Store biometric data for a voter.
    
    Args:
        voter_id: UUID of voter
        face_embedding: Face landmarks as list/array
        fingerprint_hash: Hashed fingerprint data
    
    Returns:
        True if enrollment successful, False otherwise
    """
    try:
        voter = Voter.query.filter_by(id=voter_id).first()
        if not voter:
            print(f"Voter not found: {voter_id}")
            return False
        
        if face_embedding is not None:
            voter.face_embedding = str(face_embedding)
        
        if fingerprint_hash is not None:
            voter.fingerprint_hash = fingerprint_hash
        
        db.session.commit()
        print(f"Biometrics enrolled for voter: {voter_id}")
        return True
    except Exception as e:
        print(f"Error enrolling biometrics: {e}")
        db.session.rollback()
        return False


def verify_voter_biometrics(voter_id: str, face_embedding: list = None, fingerprint_hash: str = None) -> dict:
    """
    Verify that provided biometrics match stored voter biometrics.
    Used during voting to ensure person hasn't changed.
    
    Returns:
        {
            "valid": bool,
            "face_match": bool or None,
            "fingerprint_match": bool or None,
            "message": str
        }
    """
    FACE_SIMILARITY_THRESHOLD = 0.85
    
    try:
        voter = Voter.query.filter_by(id=voter_id).first()
        if not voter:
            return {"valid": False, "message": "Voter not found"}
        
        face_match = True
        fingerprint_match = True
        issues = []
        
        # Verify face if provided and enrolled
        if face_embedding and voter.face_embedding:
            embedded_data = eval(voter.face_embedding)
            similarity = similarity_score(face_embedding, embedded_data)
            face_match = similarity >= FACE_SIMILARITY_THRESHOLD
            if not face_match:
                issues.append(f"Face mismatch (similarity: {similarity:.2f} < {FACE_SIMILARITY_THRESHOLD})")
        
        # Verify fingerprint if provided and enrolled
        if fingerprint_hash and voter.fingerprint_hash:
            fingerprint_match = fingerprint_hash == voter.fingerprint_hash
            if not fingerprint_match:
                issues.append("Fingerprint mismatch")
        
        valid = face_match and fingerprint_match
        
        return {
            "valid": valid,
            "face_match": face_match if face_embedding and voter.face_embedding else None,
            "fingerprint_match": fingerprint_match if fingerprint_hash and voter.fingerprint_hash else None,
            "message": "; ".join(issues) if issues else "Biometrics verified"
        }
    except Exception as e:
        return {"valid": False, "message": f"Verification error: {str(e)}"}


def mark_voter_as_voted(voter_id: str) -> bool:
    """Mark voter as already voted to prevent double voting."""
    try:
        voter = Voter.query.filter_by(id=voter_id).first()
        if not voter:
            return False
        
        voter.has_voted = True
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error marking voter as voted: {e}")
        db.session.rollback()
        return False
