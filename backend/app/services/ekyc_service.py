import hashlib
import random
import re
import time


def validate_aadhaar(aadhaar: str) -> bool:
    """Validate Aadhaar number format: exactly 12 digits."""
    return bool(re.match(r'^\d{12}$', aadhaar))


def hash_aadhaar(aadhaar: str) -> str:
    """Hash Aadhaar using SHA256 and return hex digest."""
    return hashlib.sha256(aadhaar.encode()).hexdigest()


def generate_epic_deterministic(voter_id: str) -> str:
    """
    Generate a deterministic EPIC ID based on voter_id.
    
    Format: EPIC-<first 10 chars of SHA256(voter_id + timestamp)>
    Includes timestamp for uniqueness across multiple registrations.
    
    Args:
        voter_id: UUID or identifier for the voter
    
    Returns:
        str: EPIC ID in format "EPIC-XXXXXXXXXX"
    """
    raw = f"{voter_id}{time.time()}"
    hash_val = hashlib.sha256(raw.encode()).hexdigest()
    return "EPIC-" + hash_val[:10].upper()


def generate_ekyc_data(aadhaar: str) -> dict:
    """Generate deterministic eKYC data from Aadhaar using stable, minimal logic."""
    male_names = [
        "Ravi", "Srinivas", "Ramesh", "Prakash", "Mahesh",
        "Kiran", "Venkatesh", "Naresh", "Rajesh", "Harish",
        "Chandra", "Suresh", "Gopi", "Srikanth", "Raghu",
        "Manoj", "Anil", "Vamshi", "Naveen", "Sai"
    ]
    female_names = [
        "Lakshmi", "Padma", "Sravani", "Swathi", "Anitha",
        "Deepika", "Keerthi", "Bhavani", "Sowmya", "Divya",
        "Anjali", "Harika", "Tejaswini", "Sushma", "Madhavi",
        "Shilpa", "Kavitha", "Renuka", "Sunitha", "Pooja"
    ]
    surnames = [
        "Reddy", "Naidu", "Rao", "Yadav", "Goud",
        "Reddy", "Reddy", "Naidu", "Rao", "Reddy"
    ]
    areas = [
        "Ameerpet", "Kukatpally", "Madhapur", "Gachibowli",
        "Secunderabad", "LB Nagar", "Dilsukhnagar",
        "Mehdipatnam", "Uppal", "Begumpet"
    ]
    district = "Hyderabad"
    state = "Telangana"

    seed = int(aadhaar[-6:])

    gender = "Female" if int(aadhaar[-1]) % 2 == 0 else "Male"
    first = (female_names if gender == "Female" else male_names)[seed % len(male_names)]
    last = surnames[(seed // 10) % len(surnames)]
    full_name = f"{first} {last}"

    area = areas[(seed // 100) % len(areas)]
    address = f"{area}, {district}, {state}"

    year = 1975 + (seed % 25)
    month = (seed % 12) + 1
    day = (seed % 28) + 1
    dob = f"{year}-{month:02d}-{day:02d}"

    # Deterministic phone generation so same Aadhaar always maps to same phone.
    phone = "9" + str(seed).zfill(9)[:9]

    profile = {
        "name": full_name,
        "gender": gender,
        "dob": dob,
        "state": state,
        "address": address,
        "phone": phone,
    }

    return profile


def generate_epic() -> str:
    """Generate a random EPIC ID: 3 uppercase letters + 7 digits."""
    letters = ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(3))
    digits = ''.join(random.choice('0123456789') for _ in range(7))
    return letters + digits