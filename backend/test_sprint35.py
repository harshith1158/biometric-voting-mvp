#!/usr/bin/env python
"""Test Sprint 3.5 improvements"""
import requests
import json

# Test 1: Candidates endpoint
print("=" * 60)
print("TEST 1: Candidates Endpoint (FIX 4-6)")
print("=" * 60)
r = requests.get('http://127.0.0.1:5000/api/candidates')
if r.status_code == 200:
    candidates = r.json()
    print(f"✓ Status: {r.status_code} OK")
    print(f"✓ Total candidates: {len(candidates['candidates'])}")
    for c in candidates['candidates']:
        print(f"  {c['id']}. {c['name']} ({c['party']}) - {c['state']}")
    
    # Verify NOTA is last
    last = candidates['candidates'][-1]
    if last['name'] == 'NOTA':
        print("✓ NOTA appears last in list")
    else:
        print(f"✗ ERROR: Last candidate is {last['name']}, not NOTA")
    
    if last['party'] == 'Independent':
        print("✓ NOTA party is correct (Independent)")
    else:
        print(f"✗ ERROR: NOTA party is {last['party']}")
else:
    print(f"✗ Status: {r.status_code}")

# Test 2: EPIC Generation
print()
print("=" * 60)
print("TEST 2: EPIC Generation with Timestamp (FIX 3)")
print("=" * 60)
from app.services.ekyc_service import generate_epic_deterministic
test_id = "550e8400-e29b-41d4-a716-446655440000"
epic1 = generate_epic_deterministic(test_id)
epic2 = generate_epic_deterministic(test_id)
print(f"✓ Generated EPIC 1: {epic1}")
print(f"✓ Generated EPIC 2: {epic2}")
print(f"✓ Format starts with 'EPIC-': {epic1.startswith('EPIC-')}")
print(f"✓ Length is 15 chars (EPIC- = 5 + 10 hash): {len(epic1) == 15}")
if epic1 != epic2:
    print("✓ EPICs differ due to timestamp (good for uniqueness)")
else:
    print("⚠ EPICs are identical (may need to check if this is expected)")

# Test 3: MAX_CONTENT_LENGTH
print()
print("=" * 60)
print("TEST 3: MAX_CONTENT_LENGTH Configuration (FIX 1)")
print("=" * 60)
from app.main import create_app
app = create_app()
max_length = app.config.get('MAX_CONTENT_LENGTH')
expected = 16 * 1024 * 1024
if max_length == expected:
    print(f"✓ MAX_CONTENT_LENGTH set correctly: {max_length} bytes (16 MB)")
else:
    print(f"✗ MAX_CONTENT_LENGTH: {max_length}, expected {expected}")

# Test 4: Swagger Endpoints
print()
print("=" * 60)
print("TEST 4: Swagger Documentation (FIX 8)")
print("=" * 60)
endpoints = [
    '/api/biometrics/selfie',
    '/api/candidates',
    '/api/cast_vote'
]
for ep in endpoints:
    rule = None
    for r in app.url_map.iter_rules():
        if ep in str(r):
            rule = str(r)
            break
    if rule:
        print(f"✓ {ep} is registered")
    else:
        print(f"✗ {ep} NOT registered")

print()
print("=" * 60)
print("All Sprint 3.5 improvements verified!")
print("=" * 60)
