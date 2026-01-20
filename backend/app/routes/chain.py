from flask import Blueprint, jsonify
from app.models import Block
from app.services.hash_chain import verify_chain

bp = Blueprint("chain", __name__, url_prefix="/api")


@bp.route("/chain_status", methods=["GET"])
def chain_status():
    """
    Get blockchain status
    ---
    responses:
      200:
        description: Blockchain status
        schema:
          type: object
          properties:
            length:
              type: integer
            valid:
              type: boolean
    """
    return jsonify(
        {
            "length": Block.query.count(),
            "valid": verify_chain(),
        }
    )