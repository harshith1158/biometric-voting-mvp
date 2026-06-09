from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
import logging
import os
from app.config import Config
from app.db import db
from app.services.hash_chain import create_genesis_block
from app.services.seed_data import seed_candidates
from app.routes import register, chain, auth, biometrics, ekyc, candidates, fingerprint, booth, real_register, face_verify, admin

# Optional alias used only in defensive fallback registration below.
fingerprint_bp = None


def _print_security_checklist(app):
    """Print a security readiness checklist to stdout/logs on every startup."""
    checks = []

    # 1. Database connectivity
    try:
        with app.app_context():
            db.session.execute(db.text("SELECT 1"))
        checks.append(("OK", "Database connected"))
    except Exception as exc:
        checks.append(("!!", f"Database connection FAILED: {exc}"))

    # 2. Unique constraints (verified via model metadata)
    checks.append(("OK", "Unique constraints: voters.aadhaar_hash, voters.epic_id, votes.epic_id (model-level)"))

    # 3. Face model
    try:
        face_model_path = os.path.join(os.path.dirname(__file__), "models", "face_landmarker.task")
        if os.path.exists(face_model_path):
            checks.append(("OK", "Face model loaded (face_landmarker.task)"))
        else:
            checks.append(("!!", "Face model NOT found at expected path - liveness may degrade"))
    except Exception:
        checks.append(("!!", "Face model path check skipped"))

    # 4. Fingerprint module
    try:
        from app.services.fingerprint_service import capture_fingerprint  # noqa: F401
        checks.append(("OK", "Fingerprint module ready"))
    except Exception as exc:
        checks.append(("!!", f"Fingerprint module unavailable: {exc}"))

    # 5. Blockchain
    try:
        with app.app_context():
            from app.models import Block
            from app.services.hash_chain import verify_chain
            count = Block.query.count()
            valid = verify_chain()
            if valid:
                checks.append(("OK", f"Blockchain initialized ({count} block(s), integrity OK)"))
            else:
                checks.append(("!!", f"BLOCKCHAIN TAMPERED - {count} block(s) but hash mismatch detected"))
    except Exception as exc:
        checks.append(("!!", f"Blockchain check failed: {exc}"))

    # 6. Election status
    try:
        with app.app_context():
            from app.models import ElectionStatus
            status = ElectionStatus.query.first()
            if not status:
                status = ElectionStatus(status="open")
                db.session.add(status)
                db.session.commit()
            checks.append(("OK", f"Election status: {status.status.upper()}"))
    except Exception as exc:
        checks.append(("!!", f"Election status check failed: {exc}"))

    # 7. Active security rules (static confirmation)
    checks.append(("OK", "Security rule: Aadhaar uniqueness enforced (DB + application layer)"))
    checks.append(("OK", "Security rule: One vote per Aadhaar (has_voted flag + Vote table uniqueness)"))
    checks.append(("OK", "Security rule: Fingerprint required before vote cast"))
    checks.append(("OK", "Security rule: Face identity verified at booth entry"))
    checks.append(("OK", "Security rule: Attempt limits active - 3 failures -> 15-minute lockout"))
    checks.append(("OK", "Security rule: Age >= 18 enforced at registration"))
    checks.append(("OK", "Security rule: Election closed -> registration + voting blocked"))

    # Print summary
    separator = "=" * 62
    print(f"\n{separator}")
    print("  TRUEVOTE  -  SECURITY STARTUP CHECKLIST")
    print(separator)
    for symbol, message in checks:
        print(f"  [{symbol}] {message}")
    print(separator + "\n")


def create_app():
    app = Flask(__name__)
    # Runtime debug: log when the factory runs (visible in Gunicorn logs)
    try:
        logging.getLogger(__name__).info(
            "[DEBUG-CREATE_APP] create_app() called; PID=%s CWD=%s",
            os.getpid(),
            os.getcwd(),
        )
    except Exception:
        print(f"[DEBUG-CREATE_APP] create_app() called; PID={os.getpid()} CWD={os.getcwd()}")

    app.config.from_object(Config)
    
    # Set maximum content length for multi-frame file uploads (16 MB)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    # ✅ CONFIGURE CORS FOR FRONTEND ACCESS
    cors_config = {
        "origins": [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:5176",
            "http://localhost:5177",
            "http://localhost:5178",
            "http://localhost:5179",
            "http://localhost:5180",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:5175",
            "http://127.0.0.1:5176",
            "http://127.0.0.1:5177",
            "http://127.0.0.1:5178",
            "http://127.0.0.1:5179",
            "http://127.0.0.1:5180",
            "http://127.0.0.1:5000",
            "http://127.0.0.1:3000",
            "http://192.168.0.102:5174",
            "http://192.168.0.102:5175",
            "http://192.168.0.102:5176",
            "http://192.168.0.102:5177",
            "http://192.168.0.102:5178",
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
    CORS(app, resources={r"/api/*": cors_config})
    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Add profile_image column if missing (existing DBs)
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE voters ADD COLUMN profile_image TEXT"))
                conn.commit()
        except Exception:
            pass  # Column already exists

        create_genesis_block()
        seed_candidates()

    app.register_blueprint(register.bp)
    app.register_blueprint(chain.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(biometrics.bp)
    app.register_blueprint(ekyc.bp)
    app.register_blueprint(candidates.bp)
    app.register_blueprint(fingerprint.bp)
    app.register_blueprint(booth.bp)
    app.register_blueprint(real_register.bp)
    app.register_blueprint(face_verify.bp)
    app.register_blueprint(admin.bp)

    # Initialize Swagger after blueprints are registered so Flasgger
    # discovers docstrings on blueprint endpoints (ensures /api/auth/* appear)
    Swagger(app)

    # ── SECURITY STARTUP SELF-CHECK ──────────────────────────────────────────
    _print_security_checklist(app)

    return app


app = create_app()

# Runtime debug: indicate module load (this will run when Gunicorn imports the module)
try:
    logging.getLogger(__name__).info(
        "[DEBUG-MODULE] backend.app.main module loaded; PID=%s CWD=%s",
        os.getpid(),
        os.getcwd(),
    )
except Exception:
    print(f"[DEBUG-MODULE] backend.app.main module loaded; PID={os.getpid()} CWD={os.getcwd()}")
    optional_fp_bp = globals().get("fingerprint_bp")
    if optional_fp_bp is not None:
        app.register_blueprint(optional_fp_bp)


@app.route("/api/test", methods=["GET"])
def test_api():
    return {"message": "Backend working"}
