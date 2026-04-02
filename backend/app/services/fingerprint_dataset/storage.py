import os
import pickle
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parents[3] / "data" / "fp_store"

os.makedirs(BASE_PATH, exist_ok=True)


def save_fp(voter_id, descriptors):
    path = BASE_PATH / f"{voter_id}.pkl"
    with open(path, "wb") as f:
        pickle.dump(descriptors, f)


def load_fp(voter_id):
    path = BASE_PATH / f"{voter_id}.pkl"
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)
