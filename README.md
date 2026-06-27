TRUE VOTE — The Future of Fair and Transparent Voting
Overview

TRUE VOTE is an AI-powered biometric electronic voting system designed to improve the security, transparency, and integrity of the voting process. The system combines facial liveness detection, facial identity verification, fingerprint authentication, Aadhaar-based voter registration, and blockchain-based vote auditing to ensure that every eligible voter can cast only one vote while preventing impersonation and vote tampering.

The project demonstrates how modern biometric technologies and secure system design can be integrated into an end-to-end electronic voting platform suitable for academic research and future real-world adaptation.

Features
Aadhaar-based voter registration
Real user registration with biometric enrollment
EPIC ID generation
AI-based face liveness detection
Facial identity verification
Fingerprint authentication before vote casting
One Aadhaar – One Vote enforcement
Duplicate registration prevention
Blockchain-based vote integrity
Administrative dashboard
Election result declaration
Swagger API documentation
System Modules
1. Home Module

Provides access to all major functionalities including:

Generate EPIC ID
Booth Voting
Admin Dashboard
New User Registration
2. New User Registration

Allows a new voter to register by providing:

First Name
Middle Name
Last Name
Aadhaar Number
Date of Birth
Gender
State
Mobile Number

The system validates:

Aadhaar format
Age (18 years or above)
Duplicate Aadhaar
Face liveness
Face enrollment

Once verified, the user's biometric data and profile information are securely stored.

3. EPIC ID Generation

Registered users generate their EPIC ID by:

Entering Aadhaar number
Completing liveness verification
Passing facial identity verification

If authentication succeeds, the system generates or retrieves the existing EPIC ID.

4. Booth Verification

The voter enters:

Aadhaar Number or EPIC ID

The system verifies:

Registered voter details
Facial identity
Voting eligibility

If the voter has already voted, access is denied.

5. Voting Module

The voter selects a candidate.

Before the vote is recorded, fingerprint authentication is performed.

After successful verification:

Vote is stored
Blockchain entry is created
Voting status is updated
6. Admin Module

The administrator can:

Monitor election activity
View registered voters
Verify blockchain integrity
Declare election results
Close the election
Project Workflow
Home
 │
 ├── New User Registration
 │       │
 │       ├── Aadhaar Validation
 │       ├── Age Verification
 │       ├── Face Liveness
 │       ├── Face Enrollment
 │       └── Save User
 │
 ├── Generate EPIC ID
 │       │
 │       ├── Aadhaar Verification
 │       ├── Liveness Detection
 │       ├── Face Identity Verification
 │       └── Generate EPIC
 │
 ├── Booth Verification
 │       │
 │       ├── Retrieve Voter
 │       ├── Verify Eligibility
 │       └── Proceed to Voting
 │
 ├── Candidate Selection
 │       │
 │       ├── Fingerprint Verification
 │       ├── Record Vote
 │       └── Update Blockchain
 │
 └── Admin Dashboard
         │
         ├── Monitor Election
         ├── Verify Blockchain
         └── Declare Results
Technologies Used
Frontend
React.js
Vite
Tailwind CSS
Axios
Backend
Python
Flask
SQLAlchemy
SQLite
Artificial Intelligence & Biometrics
MediaPipe Face Mesh
OpenCV
DeepFace / ArcFace
NumPy
Security
SHA-256 Hashing
Blockchain
Hardware
Webcam
SecuGen Hamster Pro 20 Fingerprint Scanner
Core Algorithms
Face Liveness Detection

MediaPipe Face Mesh detects facial landmarks, while the Eye Aspect Ratio (EAR) algorithm identifies natural eye blinks and head movement to ensure that the user is physically present.

Facial Identity Verification

The system captures multiple face samples during registration and verification.

Face embeddings are generated using DeepFace/ArcFace and compared using cosine distance. Identity is confirmed only when the similarity score satisfies the configured threshold.

Fingerprint Authentication

Fingerprint templates are securely associated with each registered voter. Authentication is required before a vote can be cast.

Blockchain Integrity

Every vote is stored as a blockchain block containing:

Vote information
Timestamp
Previous block hash
Current block hash

This enables verification of vote integrity and detection of tampering.

Database Design
Voters

Stores:

Personal details
Aadhaar hash
Mobile number
EPIC ID
Face embeddings
Profile image
Fingerprint hash
Voting status
Votes

Stores:

Candidate selection
Voter hash
Timestamp
Blockchain hash
Blockchain

Stores:

Block index
Previous hash
Current hash
Timestamp
Security Measures

The system enforces several security mechanisms:

One Aadhaar per voter
One EPIC ID per voter
One vote per voter
Face liveness detection
Facial identity verification
Fingerprint authentication
SHA-256 hashing
Blockchain verification
Duplicate registration prevention
Duplicate voting prevention

Project Structure:

TRUE-VOTE/
│
├── backend/
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── utils/
│   ├── data/
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── assets/
│
├── database/
│
├── docs/
│
├── README.md
└── requirements.txt

Installation
Clone the repository:

git clone https://github.com/your-username/true-vote.git
cd true-vote

Backend Setup
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python main.py

Frontend Setup
cd frontend

npm install

npm run dev

Default URLs

Frontend:
http://localhost:5173

Backend:
http://127.0.0.1:5000

Swagger Documentation:
http://127.0.0.1:5000/docs

Future Enhancements
Cloud deployment
PostgreSQL database
Real OTP gateway integration
UIDAI verification support
Passive liveness detection
Mobile application
Multi-language interface
Role-based authentication
Advanced audit logging
Performance optimization through embedding caching
Limitations
Prototype implementation intended for academic demonstration
Performance depends on camera quality and lighting conditions
Uses local biometric hardware
UIDAI integration is not included
Real fingerprint infrastructure requires certified hardware and SDK support

## License

This project is licensed under the **MIT License**.

You are free to use, modify, distribute, and build upon this project in accordance with the terms of the MIT License. See the `LICENSE` file in the root of this repository for the complete license text.

© 2025 TRUE VOTE Project Contributors.

## Authors

**TRUE VOTE – The Future of Fair and Transparent Voting**

Developed as a Final Year Major Project for the Bachelor of Technology (B.Tech) degree in Computer Engineering.

### Development Team

* Frontend Engineer
* Backend & AI Engineer
* Data Engineer

### Acknowledgements

This project was developed for academic and research purposes to demonstrate the integration of biometric authentication, secure system design, and blockchain technology in electronic voting systems.

Special thanks to our project supervisor, faculty members, and the Department of Computer Science & Engineering for their guidance and support throughout the development of this project.




