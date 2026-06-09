import json
import logging
import os
from flask import Blueprint, request, jsonify
from app.db import db
from app.models import Voter
from app.services.biometric_service import load_image_from_bytes, save_live_face, verify_identity_strict, verify_identity_multiframe

logger = logging.getLogger(__name__)
bp = Blueprint("face_verify", __name__, url_prefix="/api/face")


@bp.route("/verify", methods=["POST"])
def verify_face():
    """
    Verify live face against stored voter face image using DeepFace.
    
    STRICT IDENTITY VERIFICATION - verifies the person voting/registering is the same
    person who registered their face during EPIC generation.
    
    Accepts either:
    - epic_id (for booth voting)
    - voter_id (for EPIC generation liveness)
    
    Returns: pass/fail based on DeepFace.verify() result with enforce_detection=True.
    """
    logger.info("[FACE_VERIFY] /api/face/verify POST request")
    
    try:
        # Get epic_id OR voter_id from request
        epic_id = request.form.get("epic_id")
        voter_id = request.form.get("voter_id")
        
        if not epic_id and not voter_id:
            logger.warning("[FACE_VERIFY] Missing both epic_id and voter_id")
            return jsonify({"error": "epic_id or voter_id required"}), 400
        
        lookup_id = epic_id or voter_id
        logger.info(f"[FACE_VERIFY] Processing verification for {('epic_id' if epic_id else 'voter_id')}: {lookup_id}")
        
        # Find voter by EPIC or voter_id
        if epic_id:
            voter = Voter.query.filter_by(epic_id=epic_id).first()
        else:
            import uuid
            try:
                voter_uuid = uuid.UUID(voter_id)
                voter = Voter.query.filter_by(id=voter_uuid).first()
            except ValueError:
                logger.warning(f"[FACE_VERIFY] Invalid voter_id format: {voter_id}")
                return jsonify({"error": "Invalid voter_id format"}), 400
        
        if not voter:
            logger.warning(f"[FACE_VERIFY] Voter not found for {('epic_id' if epic_id else 'voter_id')}: {lookup_id}")
            return jsonify({"error": "Voter not found"}), 404
        
        # Check if voter already voted (only for booth voting with epic_id)
        if epic_id and voter.has_voted:
            logger.warning(f"[FACE_VERIFY] Access denied - voter {epic_id} already voted")
            return jsonify({"error": "You have already voted. Access denied."}), 403
        
        # Get stored face image path from voter record
        if not voter.face_embedding:
            logger.error(f"[FACE_VERIFY] No stored face image for {lookup_id}")
            return jsonify({"error": "Face not registered for this account"}), 400
        
        stored_face_path = voter.face_embedding
        
        if not os.path.exists(stored_face_path):
            logger.error(f"[FACE_VERIFY] Stored face image not found: {stored_face_path}")
            return jsonify({"error": "Stored face image file missing"}), 500
        
        logger.info(f"[FACE_VERIFY] Loaded stored face image: {stored_face_path}")
        print(f"[FACE_VERIFY] Registration face path: {stored_face_path}")
        
        # --- Multi-frame path (preferred) ---
        frames_files = request.files.getlist('frames')
        single_frame_file = request.files.get('frame')
        
        if frames_files:
            # Read all non-empty frame bytes
            frame_bytes_list = []
            for ff in frames_files:
                data = ff.read()
                if len(data) > 0:
                    frame_bytes_list.append(data)
            
            if not frame_bytes_list:
                logger.error("[FACE_VERIFY] All uploaded frames are empty")
                return jsonify({"error": "All uploaded frames are empty"}), 400
            
            logger.info(f"[FACE_VERIFY] Running multi-frame verification ({len(frame_bytes_list)} frames)")
            print(f"\n[FACE_VERIFY] {'='*80}")
            print(f"[FACE_VERIFY] MULTI-FRAME STRICT IDENTITY VERIFICATION")
            print(f">>> DEEPFACE VERIFY CALLED")
            print(f"STORED IMAGE: {stored_face_path}")
            print(f"LIVE IMAGE: multi-frame ({len(frame_bytes_list)} frames)")
            print(f"STEP: Identity verification starting")

            # Load pre-computed Facenet embeddings for fast path (Part 1→3 pipeline)
            stored_embeddings = None
            if voter.face_embeddings_json:
                try:
                    stored_embeddings = json.loads(voter.face_embeddings_json)
                    logger.info(f"[FACE_VERIFY] Loaded {len(stored_embeddings)} cached embeddings")
                except Exception as _je:
                    logger.warning(f"[FACE_VERIFY] Could not parse face_embeddings_json: {_je}")

            result = verify_identity_multiframe(stored_face_path, frame_bytes_list,
                                                stored_embeddings=stored_embeddings)
            verified = result.get('verified', False)
            distance = result.get('distance', 1.0)
            err_msg = result.get('error')
            result_status = result.get('status', 'failed')

            logger.info(
                f"[FACE_VERIFY] Multi-frame result: verified={verified}, "
                f"distance={distance:.4f}, status={result_status}, frames_used={result.get('frames_used', 0)}"
            )
            print(f"STEP: Identity result: {verified}")

            # Retry response (borderline match — Part 4)
            if result_status == 'retry':
                logger.warning(f"[FACE_VERIFY] BORDERLINE — requesting retry for {lookup_id}")
                print(f">>> BORDERLINE MATCH - RETRY REQUESTED")
                print(f"[FACE_VERIFY] {'='*80}\n")
                return jsonify({
                    "status": "retry",
                    "message": result.get('message', 'Please look straight and try again'),
                    "verified": False,
                    "distance": round(distance, 4),
                    "distances": result.get('distances', []),
                    "frames_used": result.get('frames_used', 0),
                }), 400

            if not verified:
                logger.error(f"[FACE_VERIFY] IDENTITY MISMATCH - BLOCKED")
                print(f">>> FACE MISMATCH - BLOCKING")
                print(f"[FACE_VERIFY] {'='*80}\n")
                return jsonify({
                    "status": "fail",
                    "error": err_msg or "Face mismatch. Identity verification failed.",
                    "verified": False,
                    "distance": round(distance, 4),
                    "distances": result.get('distances', []),
                    "frames_used": result.get('frames_used', 0),
                }), 400
            
            logger.info(f"[FACE_VERIFY] Identity verified for {lookup_id}, distance={distance:.4f}")
            print(f">>> FACE MATCH - ALLOWED")
            print(f"[FACE_VERIFY] {'='*80}\n")
            return jsonify({
                "status": "pass",
                "message": "Identity verified - Same person confirmed",
                "verified": True,
                "distance": round(distance, 4),
                "distances": result.get('distances', []),
                "frames_used": result.get('frames_used', 0),
            }), 200
        
        # --- Single-frame fallback path (backward compat) ---
        if not single_frame_file:
            logger.warning("[FACE_VERIFY] No frame(s) uploaded")
            return jsonify({"error": "No frame(s) uploaded"}), 400
        
        frame_bytes = single_frame_file.read()
        if len(frame_bytes) == 0:
            logger.error("[FACE_VERIFY] Empty frame uploaded")
            return jsonify({"error": "Empty frame"}), 400
        
        # STRICT: Save live face with MANDATORY face detection
        try:
            frame_image = load_image_from_bytes(frame_bytes)
            live_face_path = save_live_face(frame_image)
            
            if not live_face_path:
                logger.error("[FACE_VERIFY] BLOCK: Could not save live face - STRICT face detection failed")
                print(f"[FACE_VERIFY] BLOCKED: Live face not detected or multiple faces detected")
                return jsonify({"error": "Face not detected in live capture - only 1 face allowed"}), 400
            
            logger.info(f"[FACE_VERIFY] Saved live face image: {live_face_path}")
            print(f"[FACE_VERIFY] Saved live image: {live_face_path}")
        except Exception as e:
            logger.error(f"[FACE_VERIFY] Error saving live face: {str(e)}", exc_info=True)
            print(f"[FACE_VERIFY] EXCEPTION saving live face: {str(e)}")
            return jsonify({"error": "Could not process live frame"}), 400
        
        # STRICT: Identity verification using DeepFace with enforce_detection=True
        try:
            print(f"\n[FACE_VERIFY] {'='*80}")
            print(f"[FACE_VERIFY] STRICT IDENTITY VERIFICATION")
            result = verify_identity_strict(stored_face_path, live_face_path)
            verified = result.get('verified', False)
            distance = result.get('distance', 1.0)
            error = result.get('error')
            
            logger.info(f"[FACE_VERIFY] Verification result: verified={verified}, distance={distance:.4f}")
            
            # STRICT: BLOCK if verification fails - NO EXCEPTIONS, NO FALLBACK
            if not verified:
                logger.error(f"[FACE_VERIFY] ✗ IDENTITY VERIFICATION BLOCKED")
                if error:
                    logger.error(f"[FACE_VERIFY] Error: {error}")
                print(f"[FACE_VERIFY] ✗ IDENTITY MISMATCH - VERIFICATION BLOCKED")
                print(f"[FACE_VERIFY] {'='*80}\n")
                return jsonify({
                    "status": "fail",
                    "error": "Identity verification failed. Different person detected.",
                    "verified": False,
                    "distance": round(distance, 4)
                }), 400
            
            # Verification PASSED - Same person confirmed
            logger.info(f"[FACE_VERIFY] ✓ Identity verified for {lookup_id}, distance={distance:.4f}")
            print(f"[FACE_VERIFY] ✓ IDENTITY CONFIRMED - Same person")
            print(f"[FACE_VERIFY] {'='*80}\n")
            return jsonify({
                "status": "pass",
                "message": "Identity verified - Same person confirmed",
                "verified": True,
                "distance": round(distance, 4)
            }), 200
        
        except Exception as e:
            logger.error(f"[FACE_VERIFY] Verification exception: {type(e).__name__}: {str(e)}", exc_info=True)
            print(f"[FACE_VERIFY] ✗ VERIFICATION EXCEPTION - BLOCKED: {str(e)}")
            print(f"[FACE_VERIFY] {'='*80}\n")
            return jsonify({"error": f"Identity verification failed: {str(e)}"}), 500
        
        finally:
            # Clean up temporary live face image
            if live_face_path and os.path.exists(live_face_path):
                try:
                    logger.debug(f"[FACE_VERIFY] Cleaning up live image: {live_face_path}")
                    os.remove(live_face_path)
                except Exception as cleanup_error:
                    logger.warning(f"[FACE_VERIFY] Could not delete live image: {str(cleanup_error)}")
    
    except Exception as e:
        logger.error(f"[FACE_VERIFY] Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Verification error: {str(e)}"}), 500


@bp.route("/verify-epic", methods=["POST"])
def verify_epic_with_face():
    """
    Acknowledge face capture during EPIC generation (post-registration).
    
    Face was already captured and stored during liveness check.
    This endpoint just confirms receipt of face for EPIC generation.
    """
    logger.info("[FACE_VERIFY] /api/face/verify-epic POST request")
    
    try:
        # Get voter_id from request
        voter_id = request.form.get("voter_id")
        if not voter_id:
            logger.warning("[FACE_VERIFY] Missing voter_id")
            return jsonify({"error": "voter_id required"}), 400
        
        # Get image frame from request
        if "frame" not in request.files:
            logger.warning("[FACE_VERIFY] No frame in request")
            return jsonify({"error": "No frame uploaded"}), 400
        
        frame_file = request.files["frame"]
        frame_bytes = frame_file.read()
        
        if len(frame_bytes) == 0:
            logger.error("[FACE_VERIFY] Empty frame uploaded")
            return jsonify({"error": "Empty frame"}), 400
        
        logger.info(f"[FACE_VERIFY] Processing frame for voter_id: {voter_id}, size: {len(frame_bytes)} bytes")
        
        # Validate face can be detected
        try:
            frame_image = load_image_from_bytes(frame_bytes)
            face_path = save_face_image(frame_image, f"{voter_id}_epic_confirm")
            
            if not face_path:
                logger.warning("[FACE_VERIFY] Could not detect face in frame")
                return jsonify({"error": "Face not detected in frame"}), 400
            
            logger.info(f"[FACE_VERIFY] ✓ Face detected and validated for voter {voter_id}")
            
            # Clean up temporary file
            if os.path.exists(face_path):
                try:
                    os.remove(face_path)
                except:
                    pass
            
            return jsonify({
                "status": "success",
                "message": "Face validated - EPIC generation confirmed"
            }), 200
        
        except Exception as e:
            logger.error(f"[FACE_VERIFY] Error validating face: {str(e)}")
            return jsonify({"error": "Could not process frame"}), 400
    
    except Exception as e:
        logger.error(f"[FACE_VERIFY] Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error: {str(e)}"}), 500
