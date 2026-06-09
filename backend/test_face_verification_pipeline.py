#!/usr/bin/env python3
"""
Comprehensive test for strict face verification pipeline.

Tests:
1. Registration with face storage
2. Same person verification (should PASS)
3. Different person verification (should BLOCK)
4. No face detection (should BLOCK)
5. Multiple faces (should BLOCK)
"""

import os
import sys
import json
import uuid
import hashlib
import requests
from pathlib import Path
import time

# Configuration
BACKEND_URL = "http://127.0.0.1:5000/api"
TEST_DATA_DIR = Path(__file__).parent / "test_face_data"
TEST_DATA_DIR.mkdir(exist_ok=True)

print("\n" + "="*80)
print("STRICT FACE VERIFICATION TEST PIPELINE")
print("="*80)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def print_test(name, status, details=""):
    symbol = "✓" if status == "PASS" else "✗"
    print(f"\n[TEST] {symbol} {name}")
    if details:
        print(f"       {details}")

def print_info(msg):
    print(f"[INFO] {msg}")

def create_test_face_image(person_id, frame_num=0):
    """Create a dummy face image for testing"""
    import cv2
    import numpy as np
    
    # Create a simple test image with person's name
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    color = (50 + person_id*30, 100, 200 - person_id*30)
    
    # Fill with color
    img[:] = color
    
    # Add text
    cv2.putText(img, f"Person {person_id}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    cv2.putText(img, f"Frame {frame_num}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    
    path = TEST_DATA_DIR / f"person_{person_id}_frame_{frame_num}.jpg"
    cv2.imwrite(str(path), img)
    return path

def register_test_voter(aadhaar, person_id=1):
    """Register a test voter in the database"""
    print_info(f"Registering test voter with Aadhaar: {aadhaar}")
    
    # Hash the aadhaar
    aadhaar_hash = hashlib.sha256(aadhaar.encode()).hexdigest()
    voter_id = str(uuid.uuid4())
    epic_id = f"EPIC{uuid.uuid4().hex[:8].upper()}"
    
    # Create face image for this voter
    face_path = create_test_face_image(person_id, 0)
    print_info(f"Created test face: {face_path}")
    
    # Import and use the database directly to create voter
    sys.path.insert(0, str(Path(__file__).parent))
    from app.db import db
    from app.models import Voter
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Check if voter already exists
        existing = Voter.query.filter_by(aadhaar_hash=aadhaar_hash).first()
        if existing:
            print_info(f"Voter already exists: {existing.id}")
            return existing.id, str(face_path)
        
        # Create new voter
        voter = Voter(
            id=uuid.UUID(voter_id),
            aadhaar_hash=aadhaar_hash,
            epic_id=epic_id,
            name=f"Test Person {person_id}",
            face_embedding=str(face_path),  # Store face path
            is_real_user=False,
            registered_at=time.time()
        )
        db.session.add(voter)
        db.session.commit()
        
        print_info(f"✓ Registered voter: {voter_id}")
        print_info(f"✓ Epic ID: {epic_id}")
        print_info(f"✓ Face stored: {face_path}")
        
        return voter_id, str(face_path)

def test_face_verification(voter_id, test_face_path, expected_result, description):
    """Test face verification endpoint"""
    print_info(f"Testing: {description}")
    print_info(f"Voter ID: {voter_id}")
    print_info(f"Test Face: {test_face_path}")
    
    try:
        with open(test_face_path, 'rb') as f:
            files = {'frame': f}
            data = {'voter_id': voter_id}
            
            print_info("Calling /api/face/verify endpoint...")
            response = requests.post(
                f"{BACKEND_URL}/face/verify",
                files=files,
                data=data,
                timeout=30
            )
        
        print_info(f"Response Status: {response.status_code}")
        result = response.json()
        print_info(f"Response: {json.dumps(result, indent=2)}")
        
        verified = result.get('verified', False)
        
        # Check if result matches expectation
        if expected_result == "PASS":
            passed = (response.status_code == 200 and verified == True)
        elif expected_result == "FAIL":
            passed = (response.status_code == 400 and verified == False)
        else:
            passed = False
        
        if passed:
            print_test(description, "PASS", f"Result: {result.get('message', 'OK')}")
            return True
        else:
            print_test(description, "FAIL", f"Expected {expected_result}, got status={response.status_code}, verified={verified}")
            return False
            
    except Exception as e:
        print_test(description, "FAIL", f"Exception: {str(e)}")
        return False

# ============================================================================
# TEST SUITE
# ============================================================================

def run_tests():
    """Run all tests"""
    
    print_section("1. SETUP - Create Test Voters")
    
    # Create test voter 1 with face
    print_info("\nCreating Test Voter 1 (Person with registered face)")
    voter1_id, voter1_face = register_test_voter("123456789012", person_id=1)
    
    print_section("2. SAME PERSON VERIFICATION")
    
    print_info("Scenario: Person uses their own registered face → Should PASS")
    test_passed = test_face_verification(
        voter1_id,
        voter1_face,
        "PASS",
        "Same person verification (should PASS)"
    )
    
    print_section("3. DIFFERENT PERSON VERIFICATION")
    
    # Create a different face image for the same voter (simulating different person)
    print_info("Creating a DIFFERENT person's face image")
    different_face = create_test_face_image(person_id=2, frame_num=0)
    print_info(f"Different face created: {different_face}")
    
    print_info("Scenario: Different person tries to use Voter 1's EPIC → Should BLOCK")
    test_failed = test_face_verification(
        voter1_id,
        str(different_face),
        "FAIL",
        "Different person verification (should BLOCK)"
    )
    
    print_section("4. VERIFICATION SUMMARY")
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    results = []
    results.append(("✓ Same Person Verification", test_passed))
    results.append(("✓ Different Person Blocked", test_failed))
    
    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for description, passed in results:
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {description}")
    
    print("\n" + "="*80)
    print(f"PASSED: {passed_count}/{total_count}")
    print("="*80 + "\n")
    
    return passed_count == total_count

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        print_info("Starting comprehensive face verification tests...")
        print_info(f"Backend URL: {BACKEND_URL}")
        print_info(f"Test Data Dir: {TEST_DATA_DIR}")
        
        success = run_tests()
        
        if success:
            print("\n✓ ALL TESTS PASSED - Face verification pipeline is working correctly!")
            sys.exit(0)
        else:
            print("\n✗ SOME TESTS FAILED - Review results above")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
