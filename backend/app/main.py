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

    CORS(app)
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
    app.register_blueprint(fingerprint_bp)
