# STRICT FACE VERIFICATION - TEST CHECKLIST

## Overview
This checklist verifies that the biometric voting system BLOCKS unauthorized access when a different person tries to generate an EPIC ID using someone else's registered face.

## System Architecture

### Registration Phase (Stores Face)
```
User enters Aadhaar → Backend stores face in:
  File: backend/data/faces/{aadhaar_hash}.jpg
  Database: voter.face_embedding = path_to_face.jpg
```

### Verification Phase (Compares Faces)
```
During Liveness + Face Verification:
  1. Liveness check: 5 frames, blink detection, face detection
  2. Face verification: 1 fresh frame, strict DeepFace.verify() with enforce_detection=True
  3. Result: ALLOW if same person, BLOCK if different person
```

---

## Test Cases

### ✅ TEST 1: SAME PERSON - SHOULD PASS
**Objective:** Verify that the registered person can successfully generate EPIC

**Setup:**
- Person A registers with Aadhaar 999999999999
- Face is captured and stored

**Test Steps:**
1. Go to Register page
2. Enter Aadhaar: 999999999999
3. System returns: "User registered" (from check_aadhaar)
4. Proceed to Liveness
5. Person A shows face for all captures
6. Click "Start Liveness Check"
7. Keep face visible for 5 liveness frames
8. System auto-captures 1 face verification frame
9. Person A's face should be verified against registered face

**Expected Result:**
- ✅ Frontend: "Identity verified! Face matched. Generating EPIC ID..."
- ✅ Auto-navigate to Success page
- ✅ EPIC ID displayed
- ✅ Backend logs: `[IDENTITY] ✓ VERIFIED: Same person`
- ✅ DeepFace distance < 0.4

**Verification Points:**
- [ ] Liveness check passed (console: "liveness: pass")
- [ ] Face verification endpoint called with voter_id
- [ ] Response includes "verified: true"
- [ ] No error messages shown
- [ ] Auto-navigated to /success

**Browser Console Logs to Watch:**
```
[Liveness] ✓ Liveness passed - Now performing STRICT face verification
[Liveness] Calling STRICT face verification endpoint...
[Liveness] ✅ FACE IDENTITY CONFIRMED - Same person - Proceeding to EPIC
```

**Backend Console Logs to Watch:**
```
[SELFIE] ✓ Registration face saved from frame X
[FACE_VERIFY] ✓ Identity verified for {voter_id}
[IDENTITY] ✓ VERIFIED: Same person - IDENTITY CONFIRMED
```

---

### ❌ TEST 2: DIFFERENT PERSON - SHOULD BLOCK
**Objective:** Verify that a DIFFERENT person CANNOT generate EPIC using Person A's registered face

**Setup:**
- Person A already registered with face stored
- Now Person B attempts to generate EPIC using same Aadhaar

**Test Steps:**
1. Go to Register page
2. Enter same Aadhaar: 999999999999
3. System recognizes Person A's registration
4. Proceed to Liveness
5. **IMPORTANT: Person B (different face) now performs liveness**
6. Person B shows their face for 5 liveness frames
7. Click "Start Liveness Check"
8. Person B keeps their face visible for liveness
9. Person B's face is captured for verification
10. Verification compares Person B's fresh face against Person A's stored face

**Expected Result:**
- ❌ Frontend: "❌ IDENTITY VERIFICATION FAILED: Face does not match. Access denied."
- ❌ Alert shown: "Identity verification failed. The face does not match your registered face."
- ❌ Stays on Liveness page
- ❌ NO navigation to Success page
- ❌ Backend logs: `[IDENTITY] ✗ BLOCKED: Different person`
- ❌ DeepFace distance > 0.4 (different person)

**Verification Points:**
- [ ] Liveness check passed (both persons pass liveness - that's OK)
- [ ] Face verification endpoint called with voter_id
- [ ] Response includes "verified: false"
- [ ] Error message displayed
- [ ] Did NOT navigate to /success
- [ ] Page remains on Liveness

**Browser Console Logs to Watch:**
```
[Liveness] ✓ Liveness passed - Now performing STRICT face verification
[Liveness] Calling STRICT face verification endpoint...
[Liveness] ❌ FACE VERIFICATION FAILED - Different person detected
```

**Backend Console Logs to Watch:**
```
[FACE_VERIFY] ✗ IDENTITY VERIFICATION BLOCKED
[IDENTITY] ✗ BLOCKED: Different person - IDENTITY MISMATCH
Distance: 0.7234 (high distance = different person)
```

---

### ❌ TEST 3: NO FACE DETECTED - SHOULD BLOCK
**Objective:** Verify system blocks when no face is detected in live capture

**Setup:**
- Person A registered
- During face verification, no face shown

**Test Steps:**
1. Complete registration through Liveness (passes)
2. During face verification frame capture
3. **IMPORTANT: Do NOT show face - show blank/paper/wall instead**
4. System attempts face verification

**Expected Result:**
- ❌ Error: "Face not detected in live capture - only 1 face allowed"
- ❌ Backend logs: `[VERIFY] BLOCKED: Live face not detected`
- ❌ HTTP 400 response
- ❌ Stays on Liveness page

**Verification Points:**
- [ ] Liveness check passed
- [ ] Face verification called
- [ ] Response status: 400
- [ ] Error message about face detection
- [ ] Error logged in backend

**Backend Console Logs to Watch:**
```
[VERIFY] Detecting face in live image (STRICT)...
[ERROR] BLOCK: No face detected in live image
[FACE_VERIFY] BLOCK: Could not save live face - STRICT face detection failed
```

---

### ❌ TEST 4: MULTIPLE FACES - SHOULD BLOCK
**Objective:** Verify system blocks when multiple faces detected

**Setup:**
- Person A registered
- During face verification, TWO faces shown

**Test Steps:**
1. Complete registration through Liveness (passes)
2. During face verification frame capture
3. **IMPORTANT: Show TWO faces in frame (you + another person)**
4. System attempts face verification

**Expected Result:**
- ❌ Error: "Face not detected in live capture - only 1 face allowed"
- ❌ Backend logs: `[VERIFY] BLOCKED: Multiple faces detected (2)`
- ❌ HTTP 400 response
- ❌ Stays on Liveness page

**Verification Points:**
- [ ] Liveness check passed
- [ ] Face verification called
- [ ] Response status: 400
- [ ] Error message about multiple faces
- [ ] Error logged in backend

**Backend Console Logs to Watch:**
```
[VERIFY] Detecting face in live image (STRICT)...
[ERROR] BLOCK: Multiple faces detected (2) - only 1 allowed
[FACE_VERIFY] BLOCK: Could not save live face - STRICT face detection failed
```

---

## Critical Security Checks

### Face Storage Verification
- [ ] Check that face is stored at: `backend/data/faces/{aadhaar_hash}.jpg`
- [ ] Check database: `SELECT face_embedding FROM voter WHERE aadhaar_hash = ...`
- [ ] Verify file exists and is readable

### Face Comparison Verification
- [ ] Backend calls: `DeepFace.verify(registered_path, live_path, enforce_detection=True)`
- [ ] Backend logs show: Distance value and threshold comparison
- [ ] Console shows: `[IDENTITY] Distance: 0.XXXX`
- [ ] Distance < 0.4 = Same person (PASS)
- [ ] Distance > 0.4 = Different person (BLOCK)

### Strict Enforcement Verification
- [ ] No fallback if face detection fails
- [ ] No fallback if verification fails
- [ ] Blocks immediately on first failure
- [ ] Error messages are clear and actionable

---

## Test Execution Sequence

### Pre-Test
- [ ] Backend running: `python run_server.py`
- [ ] Backend logs show: "Running on http://127.0.0.1:5000"
- [ ] Frontend running: `npm run dev`
- [ ] Frontend logs show: "Local: http://localhost:5173"
- [ ] Database reset: Check if needed

### Test Sequence
1. **TEST 1** (Same Person PASS) - Use Aadhaar 999999999999
2. **TEST 2** (Different Person BLOCK) - Use same Aadhaar 999999999999 with different person
3. **TEST 3** (No Face BLOCK) - New Aadhaar, show blank during verification
4. **TEST 4** (Multiple Faces BLOCK) - New Aadhaar, show 2 faces during verification

### Post-Test
- [ ] All tests completed
- [ ] Results documented
- [ ] Issues logged if any

---

## Expected Behavior Summary

| Scenario | Registration Face | Liveness Frames | Verification Frame | Liveness Result | Verification Result | EPIC Generated |
|----------|-------------------|-----------------|--------------------|-----------------|--------------------|----------------|
| Same Person | Person A | Person A | Person A | ✅ PASS | ✅ MATCH | ✅ YES |
| Different Person | Person A | Person B | Person B | ✅ PASS | ❌ MISMATCH | ❌ NO |
| No Face | Person A | Person A | (blank) | ✅ PASS | ❌ NO FACE | ❌ NO |
| Multiple Faces | Person A | Person A | (2 people) | ✅ PASS | ❌ MULTI | ❌ NO |

---

## Troubleshooting

### Issue: Liveness passes but verification doesn't happen
**Solution:** Check browser console for voter_id. Ensure localStorage has tv_voter_id set.

### Issue: Different person verification passes (SECURITY ISSUE!)
**Solution:** 
1. Check backend logs for DeepFace distance value
2. If distance is low but different person shown - face quality issue
3. Verify DeepFace models are up-to-date
4. Test with better lighting/clearer face

### Issue: "epic_id or voter_id required" error
**Solution:** Verify voter_id is passed correctly from Register → Liveness

### Issue: Face file not found
**Solution:** Check backend/data/faces/ directory exists and has files

---

## Success Criteria

✅ **All 4 test scenarios pass as expected**
- Test 1: Same person can generate EPIC
- Test 2: Different person cannot generate EPIC
- Test 3: No face blocks access
- Test 4: Multiple faces block access

✅ **Security verified**
- System blocks on first failure
- No fallback mechanisms
- Error messages clear
- All blocking decisions logged

✅ **Performance acceptable**
- Face verification completes in < 5 seconds
- No timeout issues
- Smooth user experience

---

## Documentation & Sign-Off

Date: _____________
Tester: _____________

Test Results:
- [ ] TEST 1 PASSED
- [ ] TEST 2 PASSED
- [ ] TEST 3 PASSED
- [ ] TEST 4 PASSED

Issues Found: _____________________

Sign-Off: __________________ Date: __________

---

## References

- [Face Verification Implementation](backend/app/routes/face_verify.py)
- [Liveness Frontend](truevote-frontend/src/pages/Liveness.jsx)
- [Biometric Service](backend/app/services/biometric_service.py)
- [Manual Test Guide](MANUAL_TEST_GUIDE.md)
