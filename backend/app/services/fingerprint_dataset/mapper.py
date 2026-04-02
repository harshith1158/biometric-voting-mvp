import hashlib
from pathlib import Path


DATASET_PATH = Path(__file__).resolve().parents[3] / "data" / "fingerprints"


def get_dataset_images():
    images = []
    if not DATASET_PATH.exists():
        return images

    for file_path in DATASET_PATH.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in (".tif", ".png"):
            continue
        images.append(str(file_path.relative_to(DATASET_PATH)))

    return sorted(images)


def map_user_to_image(aadhaar_hash):
    images = get_dataset_images()

    if not images or not aadhaar_hash:
        return None

    hash_prefix = str(aadhaar_hash)[:8]
    try:
        hash_int = int(hash_prefix, 16)
    except ValueError:
        hash_int = int(hashlib.sha256(str(aadhaar_hash).encode()).hexdigest()[:8], 16)

    index = hash_int % len(images)

    return images[index]