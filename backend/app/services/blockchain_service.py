import hashlib
from datetime import datetime
from app.models import Vote


def create_block(previous_hash: str, vote_data: dict, timestamp: datetime = None) -> str:
    """
    Create a new blockchain block and compute its hash.
    
    The block hash is computed as:
    SHA256(previous_hash + vote_data + timestamp)
    
    Args:
        previous_hash: Hash of the previous block
        vote_data: Vote data to include in block
        timestamp: Timestamp for the block (default: now)
    
    Returns:
        str: SHA256 hash of the new block
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Convert vote_data to string for hashing
    vote_str = str(vote_data)
    timestamp_str = timestamp.isoformat()
    
    # Concatenate all fields
    block_data = previous_hash + vote_str + timestamp_str
    
    # Compute SHA256 hash
    block_hash = hashlib.sha256(block_data.encode()).hexdigest()
    
    return block_hash


def verify_chain() -> dict:
    """
    Verify the integrity of the entire vote blockchain.
    
    Fetches all votes ordered by creation time and recalculates
    block hashes sequentially. If any mismatch is detected,
    the chain is considered invalid.
    
    Returns:
        dict: {
            "valid": bool,
            "chain_length": int,
            "errors": list of error descriptions (if any)
        }
    """
    # Fetch all votes ordered by ID (creation order)
    votes = Vote.query.order_by(Vote.id).all()
    
    errors = []
    previous_hash = "0" * 64  # Genesis block hash (64 zeros)
    
    for idx, vote in enumerate(votes):
        # Reconstruct vote data
        vote_data = {
            "epic_id": vote.epic_id,
            "candidate_id": vote.candidate_id,
            "fingerprint_hash": vote.fingerprint_hash
        }
        
        # Recalculate block hash
        expected_hash = create_block(previous_hash, vote_data, vote.timestamp)
        
        # Check if calculated hash matches stored hash
        if expected_hash != vote.block_hash:
            errors.append(
                f"Vote {idx + 1} (ID {vote.id}): "
                f"expected {expected_hash}, got {vote.block_hash}"
            )
        
        # Update previous hash for next iteration
        previous_hash = vote.block_hash
    
    return {
        "valid": len(errors) == 0,
        "chain_length": len(votes),
        "errors": errors
    }


def get_chain_status() -> dict:
    """
    Get the current status of the vote blockchain.
    
    Returns:
        dict: {
            "length": int,
            "valid": bool,
            "last_block_hash": str or None
        }
    """
    votes = Vote.query.order_by(Vote.id).all()
    
    if not votes:
        return {
            "length": 0,
            "valid": True,
            "last_block_hash": None
        }
    
    # Verify chain
    verification = verify_chain()
    
    # Get last block hash
    last_vote = votes[-1]
    last_block_hash = last_vote.block_hash
    
    return {
        "length": len(votes),
        "valid": verification["valid"],
        "last_block_hash": last_block_hash
    }
