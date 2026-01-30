from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from app.config import Config
from app.db import db
from app.services.hash_chain import create_genesis_block
from app.routes import register, chain, auth


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        create_genesis_block()

    app.register_blueprint(register.bp)
    app.register_blueprint(chain.bp)
    app.register_blueprint(auth.bp)

    # Initialize Swagger after blueprints are registered so Flasgger
    # discovers docstrings on blueprint endpoints (ensures /api/auth/* appear)
    Swagger(app)

    return app


app = create_app()