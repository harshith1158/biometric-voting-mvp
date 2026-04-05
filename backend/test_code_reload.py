#!/usr/bin/env python3
"""Simple test of liveness endpoint to check if code reloaded"""
import requests
import json
from PIL import Image
import numpy as np
import io

def create_frame():
    a = np.ones((720, 1280, 3), dtype=np.uint8) * 200
    img = Image.fromarray(a, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95)
    buf.seek(0)
    return buf.getvalue()

# Send 5 frames
files = [('frames', (f'frame-{i+1}.jpg', create_frame(), 'image/jpeg')) for i in range(5)]
data = {'voter_id': '6ea446d7-9373-4309-b68f-82d6f0718c89'}

response = requests.post(
    'http://127.0.0.1:5000/api/biometrics/selfie',
    files=files,
    data=data,
    timeout=30
)

result = response.json()
print(json.dumps(result, indent=2))
print("\n---Checking for updated fields---")
if "UPDATED" in result.get("error", ""):
    print("✓ Code WAS reloaded - UPDATED found in error message")
else:
    print("✗ Code was NOT reloaded - UPDATED not found")

if "test_field" in result:
    print("✓ test_field is present - New code is running")
else:
    print("✗ test_field is missing - Old code is running")
