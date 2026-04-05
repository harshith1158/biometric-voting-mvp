from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
import logging
import os
from app.config import Config
from app.db import db
from app.services.hash_chain import create_genesis_block
from app.services.seed_data import seed_candidates
from app.routes import register, chain, auth, biometrics, ekyc, candidates, fingerprint, booth

# Optional alias used only in defensive fallback registration below.
fingerprint_bp = None


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

    # Initialize Swagger after blueprints are registered so Flasgger
    # discovers docstrings on blueprint endpoints (ensures /api/auth/* appear)
    Swagger(app)

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
