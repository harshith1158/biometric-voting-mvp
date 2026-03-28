import os
import json
from cryptography.fernet import Fernet


# Generate or load encryption key
# In production, this should be stored securely
_ENCRYPTION_KEY = os.environ.get('VOTE_ENCRYPTION_KEY')
if not _ENCRYPTION_KEY:
    _ENCRYPTION_KEY = Fernet.generate_key().decode()

_cipher = Fernet(_ENCRYPTION_KEY.encode() if isinstance(_ENCRYPTION_KEY, str) else _ENCRYPTION_KEY)


def get_encryption_key():
    """Get the current encryption key (for configuration/setup only)."""
    return _ENCRYPTION_KEY


def encrypt_vote(candidate_id: int, epic_id: str) -> str:
    """
    Encrypt vote data using Fernet symmetric encryption.
    
    Args:
        candidate_id: ID of the selected candidate
        epic_id: EPIC ID of the voter
    
    Returns:
        str: Encrypted vote (base64 encoded)
    """
    vote_data = {
        "candidate_id": candidate_id,
        "epic_id": epic_id
    }
    
    plaintext = json.dumps(vote_data).encode()
    encrypted = _cipher.encrypt(plaintext)
    return encrypted.decode()


def decrypt_vote(encrypted_vote: str) -> dict:
    """
    Decrypt vote data for verification.
    
    Args:
        encrypted_vote: Encrypted vote string from encrypt_vote()
    
    Returns:
        dict: {
            "candidate_id": int,
            "epic_id": str
        }
    """
    decrypted = _cipher.decrypt(encrypted_vote.encode())
    return json.loads(decrypted.decode())
