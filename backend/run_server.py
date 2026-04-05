from app import create_app
from app.db import db
from app.services.hash_chain import create_genesis_block
from app.services.seed_data import seed_candidates


app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    create_genesis_block()
    seed_candidates()
    print("Database reset complete")

app.run(debug=True)