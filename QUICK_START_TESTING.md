#!/bin/bash
# QUICK START - Face Verification Testing

# ============================================================================
# TERMINAL 1: START BACKEND
# ============================================================================
cd C:\biometric-voting-mvp\biometric-voting-mvp\backend
python run_server.py
# Wait for: "Running on http://127.0.0.1:5000"


# ============================================================================
# TERMINAL 2: START FRONTEND
# ============================================================================
cd C:\biometric-voting-mvp\biometric-voting-mvp\truevote-frontend
npm run dev
# Wait for: "Local: http://localhost:5173"


# ============================================================================
# BROWSER: OPEN AND TEST
# ============================================================================
# URL: http://localhost:5173


# ============================================================================
# TEST SCENARIOS (Use TEST_CHECKLIST.md for detailed steps)
# ============================================================================

TEST 1: Same Person - SHOULD PASS ✅
---------
Aadhaar: 999999999999
Person: Same person for registration, liveness, and verification
Expected: EPIC ID generated and displayed
Console: [Liveness] ✅ FACE IDENTITY CONFIRMED - Same person


TEST 2: Different Person - SHOULD BLOCK ❌
-----------
Aadhaar: 999999999999 (same as TEST 1)
Person: Different person for verification (but same Aadhaar)
Expected: Error message "Face does not match"
Console: [Liveness] ❌ FACE VERIFICATION FAILED - Different person detected


TEST 3: No Face - SHOULD BLOCK ❌
---------
Aadhaar: New (different from TEST 1/2)
During verification: Show blank/wall/no face
Expected: Error message "Face not detected"
Console: [VERIFY] BLOCKED: Live face not detected


TEST 4: Multiple Faces - SHOULD BLOCK ❌
------------------
Aadhaar: New (different from TEST 1/2/3)
During verification: Show 2 faces
Expected: Error message "Multiple faces"
Console: [VERIFY] BLOCKED: Multiple faces detected


# ============================================================================
# VERIFICATION CHECKLIST
# ============================================================================

After each test, verify:

✅ TEST 1 (Same Person):
   [ ] Frontend shows success message
   [ ] EPIC ID displayed on Success page
   [ ] Backend logs: [IDENTITY] ✓ VERIFIED
   [ ] Distance value < 0.4

✅ TEST 2 (Different Person):
   [ ] Frontend shows error: "Face does not match"
   [ ] Alert displayed to user
   [ ] NO navigation to Success page
   [ ] Backend logs: [IDENTITY] ✗ BLOCKED
   [ ] Distance value > 0.4

✅ TEST 3 (No Face):
   [ ] Frontend shows error: "Face not detected"
   [ ] Backend logs: [VERIFY] BLOCKED: No face detected
   [ ] Access denied

✅ TEST 4 (Multiple Faces):
   [ ] Frontend shows error: "Multiple faces"
   [ ] Backend logs: [VERIFY] BLOCKED: Multiple faces
   [ ] Access denied


# ============================================================================
# MONITORING LOGS
# ============================================================================

BACKEND TERMINAL (Success Path):
[SELFIE] ✓ Registration face saved from frame 0
[FACE_VERIFY] ✓ Identity verified for {voter_id}
[IDENTITY] ✓ VERIFIED: Same person - IDENTITY CONFIRMED

BACKEND TERMINAL (Blocking Paths):
[VERIFY] BLOCKED: Live face not detected
[VERIFY] BLOCKED: Multiple faces detected (2)
[IDENTITY] ✗ BLOCKED: Different person - IDENTITY MISMATCH

BROWSER CONSOLE (Success Path):
[Liveness] ✓ Liveness passed
[Liveness] ✅ FACE IDENTITY CONFIRMED - Same person - Proceeding to EPIC

BROWSER CONSOLE (Blocking Paths):
[Liveness] ❌ FACE VERIFICATION FAILED - Different person detected


# ============================================================================
# QUICK TROUBLESHOOTING
# ============================================================================

Q: Backend won't start?
A: pip install "numpy<2" --force-reinstall
   python run_server.py

Q: voter_id missing error?
A: Check localStorage in DevTools:
   Application → localStorage → tv_voter_id (should have UUID)

Q: Verification doesn't run?
A: Check browser console for errors
   Check backend logs for API calls

Q: Different person verification passes (BUG!)?
A: Check backend distance value in console
   If <0.4: Model accuracy issue (need better face quality)


# ============================================================================
# DOCUMENTATION FILES
# ============================================================================

MANUAL_TEST_GUIDE.md - Step-by-step guide for each scenario
TEST_CHECKLIST.md - Comprehensive checklist with verification points
IMPLEMENTATION_SUMMARY.md - Complete overview
This file - Quick reference

