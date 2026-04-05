#!/usr/bin/env python3
"""Register a test voter and test the liveness endpoint"""

import requests
import io
from PIL import Image
import numpy as np
import json
import sys

def create_test_image():
    """Create a  simple image"""
    img_array = np.ones((720, 1280, 3), dtype=np.uint8) * 200
    img = Image.fromarray(img_array, 'RGB')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    return buffer.getvalue()

def main():
    # Step 1: Register a voter
    print("=" * 60)
    print("STEP 1: Register Voter")
    print("=" * 60)
    
    reg_response = requests.post(
        "http://127.0.0.1:5000/api/register",
        json={"aadhar_number": "123456789012"},
        timeout=10
    )
    
    print(f"Register Status: {reg_response.status_code}")
    reg_data = reg_response.json()
    print(f"Register Response: {json.dumps(reg_data, indent=2)}")
    
    if reg_response.status_code != 201:
        print("✗ Registration failed!")
        return
    
    voter_id = reg_data.get('voter_id')
    print(f"✓ Registered voter: {voter_id}\n")
    
    # Step 2: Test liveness with frames
    print("=" * 60)
    print("STEP 2: Test Liveness Detection")
    print("=" * 60)
    
    files = []
    for i in range(5):
        frame_data = create_test_image()
        files.append(('frames', (f'frame-{i+1}.jpg', frame_data, 'image/jpeg')))
        print(f"Frame {i+1}: {len(frame_data)} bytes")
    
    data = {'voter_id': voter_id}
    
    print(f"\nSending request to /api/biometrics/selfie...")
    
    live_response = requests.post(
        "http://127.0.0.1:5000/api/biometrics/selfie",
        files=files,
        data=data,
        timeout=30
    )
    
    print(f"\nLiveness Status: {live_response.status_code}")
    live_data = live_response.json()
    print(f"Liveness Response: {json.dumps(live_data, indent=2)}")
    
    if live_response.status_code == 200:
        print("✓ Liveness check passed!")
    else:
        print(f"✗ Liveness check failed with status {live_response.status_code}")
        if 'error' in live_data:
            print(f"Error: {live_data['error']}")
        if 'details' in live_data:
            print(f"Details: {live_data['details']}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
