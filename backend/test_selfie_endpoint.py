#!/usr/bin/env python3
"""Test the /api/biometrics/selfie endpoint"""

import requests
import io
from PIL import Image
import numpy as np
import json
from pathlib import Path

# Test with a simple image - create a white image
def create_test_image():
    """Create a simple white RGB image"""
    img_array = np.ones((720, 1280, 3), dtype=np.uint8) * 200  # Light gray
    img = Image.fromarray(img_array, 'RGB')
    
    # Convert to JPEG bytes
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    return buffer.getvalue()

if __name__ == '__main__':
    # Test settings
    BACKEND_URL = "http://127.0.0.1:5000/api/biometrics/selfie"
    VOTER_ID = "740cb99e-2f61-4ace-b84f-6fdc24f12c2a"  # Example UUID
    
    print(f"Testing {BACKEND_URL}")
    print(f"Voter ID: {VOTER_ID}\n")
    
    # Create test frames
    files = []
    for i in range(5):
        frame_data = create_test_image()
        files.append(('frames', (f'frame-{i+1}.jpg', frame_data, 'image/jpeg')))
        print(f"Created frame {i+1}: {len(frame_data)} bytes")
    
    # Prepare multipart form data
    data = {'voter_id': VOTER_ID}
    
    print(f"\nSending request with {len(files)} frames...\n")
    
    try:
        response = requests.post(
            BACKEND_URL,
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code != 200:
            print(f"\n❌ Request failed with status {response.status_code}")
        else:
            print(f"\n✓ Request succeeded!")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
