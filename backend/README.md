FINAL SECURITY HARDENING + SERVER-SIDE TESTING WORKFLOW

STEP 1 - RESET DB

python reset_db.py

STEP 2 - START BACKEND

cd backend
flask run

STEP 3 - RUN SMOKE TEST

python smoke_test.py

Expected:
- chain_status works
- register works
- vote triggers fingerprint capture

STEP 4 - SECURITY TEST (CRITICAL)

Send fake fingerprint in payload:

POST /api/cast_vote
{
	"epic_id": "test",
	"candidate_id": 1,
	"fingerprint_hash": "fake"
}

Expected:
- Backend ignores fingerprint_hash from request
- Backend forces live fingerprint scan on server

STEP 5 - REAL DEVICE TEST

1. Register with RIGHT thumb
2. Vote with RIGHT thumb -> PASS
3. Vote with LEFT thumb -> FAIL

STEP 6 - FRONTEND TEST

- Click vote
- Scanner triggers automatically
- No stored fingerprint is used for /api/cast_vote
