import os
import shutil
from pathlib import Path

from app import create_app
from app.db import db
from app.services.seed_data import seed_candidates
from app.services.hash_chain import create_genesis_block


def _force_writable_and_retry(func, path, exc_info):
    try:
        os.chmod(path, 0o700)
        func(path)
    except Exception as exc:
        print(f"[RESET] Could not remove {path}: {exc}")


def _safe_remove_file(file_path: Path) -> None:
    if not file_path.exists():
        return
    try:
        file_path.unlink()
        print(f"[RESET] Removed DB file: {file_path}")
    except Exception as exc:
        print(f"[RESET] Could not remove {file_path}: {exc}")


def _safe_clear_dir(dir_path: Path) -> None:
    if not dir_path.exists() or not dir_path.is_dir():
        return
    for child in dir_path.iterdir():
        try:
            if child.is_dir():
                shutil.rmtree(child, onerror=_force_writable_and_retry)
            else:
                os.chmod(child, 0o600)
                child.unlink()
        except Exception as exc:
            print(f"[RESET] Could not remove {child}: {exc}")
    print(f"[RESET] Cleared directory: {dir_path}")


backend_dir = Path(__file__).resolve().parent

# Remove all likely runtime SQLite files used by this project.
db_search_roots = [
    backend_dir,
    backend_dir / "instance",
]
seen_db_files = set()
for root in db_search_roots:
    if not root.exists():
        continue
    for pattern in ("*.db", "*.sqlite", "*.sqlite3"):
        for db_file in root.glob(pattern):
            if db_file not in seen_db_files:
                seen_db_files.add(db_file)
                _safe_remove_file(db_file)

# Clear persisted biometric artifacts to avoid stale cross-run behavior.
_safe_clear_dir(backend_dir / "data" / "faces")
_safe_clear_dir(backend_dir / "data" / "face_images")
_safe_clear_dir(backend_dir / "data" / "fingerprints")
_safe_clear_dir(backend_dir / "data" / "fp_store")

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    create_genesis_block()
    seed_candidates()

    print("[RESET] Database reset and seeded successfully")
