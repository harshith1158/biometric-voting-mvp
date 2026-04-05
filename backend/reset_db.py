from app import create_app
from app.db import db
from app.services.seed_data import seed_candidates
from app.services.hash_chain import create_genesis_block

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    create_genesis_block()
    seed_candidates()
    print("Database reset and seeded successfully")
