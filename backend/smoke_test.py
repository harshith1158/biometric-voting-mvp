import requests

BASE = "http://127.0.0.1:5000"


def test_chain():
    print("Testing chain...")
    print(requests.get(f"{BASE}/api/chain_status").json())


def test_register():
    print("Testing register...")
    res = requests.post(f"{BASE}/api/register", json={
        "aadhaar": "123456789012",
        "phone": "9999999999"
    })
    print(res.json())
    return res.json().get("epic_id")


def test_vote(epic):
    print("Testing vote (fingerprint required)...")
    res = requests.post(f"{BASE}/api/cast_vote", json={
        "epic_id": epic,
        "candidate_id": 1
    })
    print(res.json())


if __name__ == "__main__":
    epic = test_register()
    test_chain()
    if epic:
        test_vote(epic)
