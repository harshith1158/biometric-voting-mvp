from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///voting.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

db = SQLAlchemy()

def reset_db():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables recreated successfully.")

if __name__ == "__main__":
    reset_db()
