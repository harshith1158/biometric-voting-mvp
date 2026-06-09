import hashlib
from datetime import datetime
from app.models import Block
from app.db import db


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def get_last_block():
    return Block.query.order_by(Block.id.desc()).first()


def create_genesis_block():
    if Block.query.count() == 0:
        timestamp = datetime.utcnow().isoformat()
        genesis = Block(
            previous_hash="0" * 64,
            data_hash=sha256("GENESIS"),
            block_hash=sha256("GENESIS" + "0" * 64 + timestamp),
            hash_timestamp=timestamp,
        )
        db.session.add(genesis)
        db.session.commit()


def append_block(data: str) -> str:
    last = get_last_block()
    timestamp = datetime.utcnow().isoformat()
    data_hash = sha256(data)
    block_hash = sha256(last.block_hash + data_hash + timestamp)

    block = Block(
        previous_hash=last.block_hash,
        data_hash=data_hash,
        block_hash=block_hash,
        hash_timestamp=timestamp,
    )
    db.session.add(block)
    db.session.commit()
    return block_hash


def verify_chain() -> bool:
    blocks = Block.query.order_by(Block.id).all()
    for i in range(1, len(blocks)):
        recalculated = sha256(
            blocks[i - 1].block_hash
            + blocks[i].data_hash
            + blocks[i].hash_timestamp
        )
        if recalculated != blocks[i].block_hash:
            return False
    return True


def verify_chain_detailed() -> dict:
    """
    Recompute every block hash and report which blocks have been tampered with.

    Returns:
        {
            "valid": bool,
            "total_blocks": int,
            "tampered_count": int,
            "tampered_blocks": [
                {"index": int, "block_id": int, "stored_hash": str, "expected_hash": str, "timestamp": str},
                ...
            ]
        }
    """
    blocks = Block.query.order_by(Block.id).all()
    tampered = []
    for i in range(1, len(blocks)):
        expected = sha256(
            blocks[i - 1].block_hash
            + blocks[i].data_hash
            + blocks[i].hash_timestamp
        )
        if expected != blocks[i].block_hash:
            tampered.append(
                {
                    "index": i,
                    "block_id": blocks[i].id,
                    "stored_hash": blocks[i].block_hash,
                    "expected_hash": expected,
                    "timestamp": blocks[i].hash_timestamp,
                }
            )
    return {
        "valid": len(tampered) == 0,
        "total_blocks": len(blocks),
        "tampered_count": len(tampered),
        "tampered_blocks": tampered,
    }