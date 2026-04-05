import requests
import json
import random
from pathlib import Path

BASE = "http://127.0.0.1:5000/api"
IMAGE_PATH = Path("backend/real_test.jpg")

results = []

def log(name, passed, detail):
    results.append({"test": name, "passed": bool(passed), "detail": detail})


def register(aadhaar):
    return requests.post(f"{BASE}/register", json={"aadhar_number": aadhaar}, timeout=20)


def selfie(voter_id, image_bytes):
    files = []
    for i in range(5):
        files.append(("frames", (f"frame-{i+1}.jpg", image_bytes, "image/jpeg")))
    data = {"voter_id": voter_id}
    return requests.post(f"{BASE}/biometrics/selfie", files=files, data=data, timeout=60)


def cast_vote(epic_id, candidate_id=1):
    return requests.post(f"{BASE}/cast_vote", json={"epic_id": epic_id, "candidate_id": candidate_id}, timeout=60)

# Precheck
requests.get(f"{BASE}/candidates", timeout=10).raise_for_status()

suffix = str(random.randint(100000, 999999))
a1 = "91" + suffix + "0001"
a2 = "91" + suffix + "0002"

# TEST 1: New Aadhaar -> PASS -> EPIC generated
r1 = register(a1)
try:
    d1 = r1.json()
except Exception:
    d1 = {"raw": r1.text}
pass1 = (r1.status_code == 201 and bool(d1.get("epic_id")))
log("TEST 1: New Aadhaar registration", pass1, {"status": r1.status_code, "response": d1})

# TEST 2: Same Aadhaar again -> FAIL "Aadhaar already registered"
r2 = register(a1)
try:
    d2 = r2.json()
except Exception:
    d2 = {"raw": r2.text}
pass2 = (r2.status_code == 400 and d2.get("error") == "Aadhaar already registered")
log("TEST 2: Duplicate Aadhaar", pass2, {"status": r2.status_code, "response": d2})

# TEST 3: Different Aadhaar + same face -> FAIL "Face already registered"
# Requires image-based liveness pass at least once
if not IMAGE_PATH.exists():
    log("TEST 3: Duplicate face", False, {"blocked": f"Image file not found: {IMAGE_PATH}"})
else:
    img = IMAGE_PATH.read_bytes()
    # Register second voter
    r3reg = register(a2)
    d3reg = r3reg.json()
    if r1.status_code != 201 or not d1.get("voter_id") or r3reg.status_code != 201 or not d3reg.get("voter_id"):
        log("TEST 3: Duplicate face", False, {
            "blocked": "Could not create both voters needed for face duplicate test",
            "v1": {"status": r1.status_code, "response": d1},
            "v2": {"status": r3reg.status_code, "response": d3reg},
        })
    else:
        s1 = selfie(d1["voter_id"], img)
        j1 = s1.json()
        s2 = selfie(d3reg["voter_id"], img)
        j2 = s2.json()
        pass3 = (s2.status_code == 400 and j2.get("error") == "Face already registered")
        log("TEST 3: Duplicate face", pass3, {
            "first_selfie": {"status": s1.status_code, "response": j1},
            "second_selfie": {"status": s2.status_code, "response": j2},
        })

# TEST 4: Same fingerprint -> FAIL "Fingerprint already registered"
# TEST 5: Vote once PASS, vote again FAIL "Already voted"
# These depend on RD Service / fingerprint hardware availability.
if r1.status_code == 201 and d1.get("epic_id"):
    v1 = cast_vote(d1["epic_id"], 1)
    try:
        v1j = v1.json()
    except Exception:
        v1j = {"raw": v1.text}

    # test 5 second vote
    v2 = cast_vote(d1["epic_id"], 2)
    try:
        v2j = v2.json()
    except Exception:
        v2j = {"raw": v2.text}

    pass5 = (v1.status_code in (200, 201) and v2.status_code == 400 and v2j.get("error") == "Already voted")
    log("TEST 5: Vote once then duplicate vote", pass5, {
        "first_vote": {"status": v1.status_code, "response": v1j},
        "second_vote": {"status": v2.status_code, "response": v2j},
    })

    # For test 4, if first vote itself fails due RD service, report blocked
    if v1.status_code >= 500 and isinstance(v1j, dict) and "RD Service" in json.dumps(v1j):
        log("TEST 4: Duplicate fingerprint", False, {
            "blocked": "RD Service/Fingerprint hardware unavailable, cannot execute fingerprint uniqueness test end-to-end",
            "first_vote": {"status": v1.status_code, "response": v1j},
        })
    else:
        # We cannot force same fingerprint via API without hardware input; report best-effort
        log("TEST 4: Duplicate fingerprint", False, {
            "blocked": "Cannot force identical fingerprint via API automation without controlled RD capture input",
            "note": "Endpoint-level duplicate fingerprint check is in place; manual hardware test required.",
        })
else:
    log("TEST 4: Duplicate fingerprint", False, {"blocked": "No valid EPIC from TEST 1 to proceed"})
    log("TEST 5: Vote once then duplicate vote", False, {"blocked": "No valid EPIC from TEST 1 to proceed"})

print(json.dumps(results, indent=2))
