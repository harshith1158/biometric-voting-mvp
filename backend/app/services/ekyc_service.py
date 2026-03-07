import hashlib
import random
import re
from datetime import datetime, timedelta


def validate_aadhaar(aadhaar: str) -> bool:
    """Validate Aadhaar number format: exactly 12 digits."""
    return bool(re.match(r'^\d{12}$', aadhaar))


def hash_aadhaar(aadhaar: str) -> str:
    """Hash Aadhaar using SHA256 and return hex digest."""
    return hashlib.sha256(aadhaar.encode()).hexdigest()


def generate_ekyc_data(aadhaar: str) -> dict:
    """Generate deterministic eKYC data based on Aadhaar hash as seed."""
    # Use Aadhaar hash as seed for deterministic randomness
    seed = int(hash_aadhaar(aadhaar), 16) % (2**32)
    random.seed(seed)

    # Name pool
    names = [
        "Arjun Reddy",
        "Rahul Sharma",
        "Priya Nair",
        "Ananya Patel",
        "Karan Mehta",
        "Vikram Singh"
    ]
    name = random.choice(names)

    # DOB: 1975-2004
    start_date = datetime(1975, 1, 1)
    end_date = datetime(2004, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    dob = start_date + timedelta(days=random_days)
    dob_str = dob.strftime("%Y-%m-%d")

    # Gender
    gender = random.choice(["Male", "Female"])

    # Address: City
    cities = [
        "Hyderabad",
        "Delhi",
        "Mumbai",
        "Chennai",
        "Bangalore",
        "Pune"
    ]
    address = random.choice(cities)

    # Phone: 9XXXXXXXXX
    phone = f"9{random.randint(100000000, 999999999)}"

    return {
        "name": name,
        "dob": dob_str,
        "gender": gender,
        "address": address,
        "phone": phone
    }


def generate_epic() -> str:
    """Generate a random EPIC ID: 3 uppercase letters + 7 digits."""
    letters = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(3))
    digits = ''.join(random.choice('0123456789') for _ in range(7))
    return letters + digits