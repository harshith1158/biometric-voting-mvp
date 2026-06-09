#!/usr/bin/env python3
"""
MANUAL TEST GUIDE: Strict Face Verification Pipeline
=====================================================

This guide tests the complete EPIC generation flow with strict face verification.

SCENARIOS TO TEST:
==================

Scenario 1: SAME PERSON - Should PASS
- Register with Person A's face
- During liveness, show Person A's face  
- During face verification, show Person A's face
- Expected: EPIC generation succeeds

Scenario 2: DIFFERENT PERSON - Should BLOCK
- Register with Person A's face
- During liveness, show Person A's face
- During face verification, show Person B's face (different person)
- Expected: BLOCK at face verification step with error "Face does not match"

Scenario 3: NO FACE DETECTED - Should BLOCK
- Register with Person A's face
- During liveness, show Person A's face
- During face verification, show no face (blank screen/paper)
- Expected: BLOCK with error "Face not detected"

Scenario 4: MULTIPLE FACES - Should BLOCK
- Register with Person A's face
- During liveness, show Person A's face
- During face verification, show multiple people
- Expected: BLOCK with error "Multiple faces detected"

SETUP INSTRUCTIONS:
===================

1. ENSURE BACKEND IS RUNNING
   - Terminal 1: cd backend && python run_server.py
   - Wait for "Running on http://127.0.0.1:5000"

2. START FRONTEND
   - Terminal 2: cd truevote-frontend && npm run dev
   - Wait for "Local: http://localhost:5173"

3. OPEN BROWSER
   - Navigate to http://localhost:5173

TESTING STEPS:
==============

TEST 1: SAME PERSON VERIFICATION (✓ PASS EXPECTED)
----------------------------------------------------
1. Go to Register page
2. Enter test Aadhaar: 999999999999
3. Click "Check Aadhaar"
4. Proceed to Fingerprint (or skip)
5. Proceed to Liveness page
6. IMPORTANT: For all captures (liveness + face verification):
   - Position your face CLEARLY in frame
   - Make sure only YOUR face is visible
7. Click "Start Liveness Check"
8. Keep face visible and still for 5 frame captures (should show 5 captured frames)
9. After liveness passes, system will capture one more frame for face verification
10. RESULT: Should show "✓ Identity verified! Face matched. Generating EPIC ID..."
11. RESULT: Success page displays EPIC ID
    
Expected Console Logs:
- [Liveness] ✓ Liveness passed
- [Liveness] Calling STRICT face verification endpoint...
- [Liveness] ✅ FACE IDENTITY CONFIRMED - Same person
- Auto-navigate to /success

TEST 2: DIFFERENT PERSON VERIFICATION (✗ SHOULD BLOCK)
-------------------------------------------------------
SETUP:
1. FIRST: Complete TEST 1 successfully with Person A
   (This creates the registration with Person A's face)

2. NEW TEST:
   a. Go back to Register page
   b. Enter SAME test Aadhaar: 999999999999
   c. System recognizes it's registered and allows proceeding
   d. Go to Liveness page

3. DIFFERENT PERSON (Person B) now performs liveness:
   a. Person B positions face in frame
   b. Click "Start Liveness Check"
   c. Person B keeps their face visible for 5 captures
   d. After liveness passes, Person B's face is captured again for verification
   e. RESULT: Should show "❌ IDENTITY VERIFICATION FAILED: Face does not match"
   f. RESULT: Should show error alert: "Identity verification failed. The face does not match your registered face."
   g. RESULT: Access is BLOCKED - cannot proceed to EPIC

Expected Console Logs:
- [Liveness] ✓ Liveness passed
- [Liveness] Calling STRICT face verification endpoint...
- [Liveness] ❌ FACE VERIFICATION FAILED - Different person detected
- NO navigation to /success

TEST 3: NO FACE DETECTION (✗ SHOULD BLOCK)
--------------------------------------------
1. Start from registered state (use same Aadhaar as TEST 1)
2. Go to Liveness page
3. For liveness captures:
   - Show your face normally (5 captures)
4. Liveness should pass
5. For face verification capture:
   - DO NOT show your face - show blank screen or paper instead
6. RESULT: Should show "❌ IDENTITY VERIFICATION FAILED: Face not detected"
7. RESULT: Access is BLOCKED

Expected Console Logs:
- [VERIFY] BLOCKED: Live face not detected

TEST 4: MULTIPLE FACES (✗ SHOULD BLOCK)
----------------------------------------
1. Start from registered state
2. Go to Liveness page
3. For liveness captures:
   - Show your face normally (5 captures)
4. Liveness should pass
5. For face verification capture:
   - Position TWO faces in frame (you + another person or mirror reflection)
6. RESULT: Should show "❌ IDENTITY VERIFICATION FAILED: Multiple faces detected"
7. RESULT: Access is BLOCKED

Expected Console Logs:
- [VERIFY] BLOCKED: Multiple faces detected

KEY VERIFICATION POINTS:
========================

✓ STRICT ENFORCEMENT - Check console logs for these patterns:

During Liveness Registration (backend):
  - [SELFIE] ✓ Registration face saved from frame X
  - [SELFIE] Saved registration image: backend/data/faces/{aadhaar_hash}.jpg

During Face Verification (backend):
  - [FACE_VERIFY] ✓ Identity verified for {voter_id}
  OR
  - [FACE_VERIFY] ✗ IDENTITY VERIFICATION BLOCKED

During Face Verification (frontend):
  - [Liveness] ✅ FACE IDENTITY CONFIRMED - Same person - Proceeding to EPIC
  OR
  - [Liveness] ❌ FACE VERIFICATION FAILED - Different person detected

✓ BLOCKING BEHAVIOR - Verify these blocks happen IMMEDIATELY:
  1. Different person: Block at face verification
  2. No face detected: Block during live face save
  3. Multiple faces: Block during face detection
  4. NO FALLBACK: Once blocked, error message shown and access denied

DEBUGGING TIPS:
===============

If you see "epic_id or voter_id required" error:
- Check browser console for voter_id value
- Make sure localStorage has 'tv_voter_id' set
- Check Register page: tv_voter_id should be logged after Aadhaar check

If face verification seems to skip:
- Check if liveness actually passed (check ear_values)
- Check console for capture frame errors
- Ensure camera permissions are allowed

If both persons pass (security issue):
- Check if BOTH registration and live face are being saved correctly
- Verify DeepFace.verify() is being called with enforce_detection=True
- Check backend logs for [IDENTITY] verification results

MONITORING BACKEND LOGS:
=========================

Watch the terminal running "python run_server.py" for these logs:

✓ Registration face saved:
  [SELFIE] ✓ Registration face saved from frame X
  [SELFIE] ✓ Voter registered with face: backend/data/faces/{hash}.jpg

✓ Identity verification passed:
  [IDENTITY] RESULT:
    - Verified: True
    - Distance: 0.1234
  [IDENTITY] ✓ VERIFIED: Same person - IDENTITY CONFIRMED

✗ Identity verification blocked:
  [IDENTITY] RESULT:
    - Verified: False
    - Distance: 0.8765
  [IDENTITY] ✗ BLOCKED: Different person - IDENTITY MISMATCH

✗ Face detection failed:
  [VERIFY] BLOCKED: Live face not detected
  [VERIFY] BLOCKED: Multiple faces detected

EXPECTED FLOW DIAGRAM:
======================

Register (Aadhaar) → OTP → Fingerprint → Liveness
                                           ↓
                              Capture 5 frames (liveness)
                                           ↓
                              Backend: save_registration_face()
                              ✓ Face detected & saved
                                           ↓
                              Liveness check passes
                                           ↓
                              Frontend: Capture fresh frame
                                           ↓
                              Backend: verify_identity_strict()
                              ✓ Face detection: 1 face found
                              ✓ DeepFace.verify(): distance < threshold
                                           ↓
                              ✅ Identity confirmed
                              ↓
                              Auto-navigate to Success
                              ↓
                              Display EPIC ID


BLOCKING FLOWS:
===============

BLOCK at Registration (Different face):
  Liveness check passes
    → Backend: save_registration_face() fails (no single face)
    → Error: "Face detection failed"
    → Cannot proceed

BLOCK at Verification (Different person):
  Liveness check passes
    → Capture fresh frame for verification
    → Backend: verify_identity_strict() called
    → DeepFace.verify(): distance > threshold (different person)
    → ❌ IDENTITY VERIFICATION BLOCKED
    → Frontend: "Face does not match" error
    → Access denied

SUCCESS INDICATORS:
===================

Frontend Success:
  ✓ Message: "Identity verified! Face matched. Generating EPIC ID..."
  ✓ Auto-navigate to /success page
  ✓ EPIC ID displayed and copyable

Backend Success:
  ✓ Console: [IDENTITY] ✓ VERIFIED: Same person
  ✓ Distance value < 0.4 (depends on model)
  ✓ HTTP 200 response with verified: true

Frontend Blocking:
  ✗ Message: "❌ IDENTITY VERIFICATION FAILED: Face does not match"
  ✗ Alert: "Identity verification failed. The face does not match your registered face."
  ✗ Stay on Liveness page
  ✗ No navigation to /success

Backend Blocking:
  ✗ Console: [IDENTITY] ✗ BLOCKED: Different person
  ✗ Distance value > 0.4
  ✗ HTTP 400 response with verified: false

NOTES:
======
- Registration face is stored at: backend/data/faces/{aadhaar_hash}.jpg
- Liveness frames are temporary and deleted after verification
- Face verification happens IMMEDIATELY after liveness (no gap)
- Uses fresh frame for verification (not liveness frames)
- DeepFace uses VGG-Face model with cosine distance metric
- Threshold is typically 0.4 but can be adjusted if needed
- All comparisons use enforce_detection=True (STRICT mode)

TEST COMPLETION:
================

All 4 scenarios should work as described for the system to be considered
production-ready:

✓ TEST 1: Same person passes (can generate EPIC)
✓ TEST 2: Different person blocked (cannot generate EPIC)
✓ TEST 3: No face blocked (cannot generate EPIC)
✓ TEST 4: Multiple faces blocked (cannot generate EPIC)

If all pass, the strict face verification system is working correctly!
"""

print(__doc__)
