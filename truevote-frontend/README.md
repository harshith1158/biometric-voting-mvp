# TRUE VOTE Frontend

A modern React + Vite + Tailwind CSS frontend for the TRUE VOTE biometric voting system.

## Features

- **Voter Registration**: Aadhaar-based registration with eKYC verification
- **Liveness Detection**: Multi-frame facial liveness check using device webcam
- **Candidate Selection**: Beautiful card-based UI for candidate selection
- **Vote Casting**: Secure vote recording with blockchain validation
- **Result Display**: Blockchain chain status verification

## Project Structure

```
src/
├── pages/
│   ├── Register.jsx   - Voter registration with eKYC
│   ├── Liveness.jsx   - Facial liveness detection
│   ├── Booth.jsx      - Candidate selection and vote casting
│   └── Result.jsx     - Vote confirmation and blockchain status
├── components/
│   ├── Navbar.jsx     - Application header
│   └── CandidateCard.jsx - Candidate selection card
├── services/
│   └── api.js         - Axios API client
├── App.jsx            - Main app with routing
├── main.jsx           - Entry point
└── index.css          - Tailwind styles
```

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Production Build

```bash
npm run build
npm run preview
```

## API Integration

The frontend connects to the Flask backend at `http://127.0.0.1:5000/api`

### Endpoints Used:
- `POST /register_voter` - Register voter with eKYC
- `POST /biometrics/selfie` - Liveness detection (multi-frame)
- `GET /candidates` - Get candidate list
- `POST /cast_vote` - Cast vote
- `GET /chain_status` - Get blockchain status

## Flow

1. **Register** → Enter Aadhaar → eKYC verification → Get EPIC
2. **Liveness** → Webcam capture → 5 frames → Blink detection
3. **Booth** → Select candidate → Confirm → Cast vote
4. **Result** → See blockchain validation and status

## Technologies

- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Axios** - HTTP requests
- **React Router** - Navigation

## Browser Requirements

- Modern browser with:
  - WebRTC support (for webcam access)
  - ES6+ support
  - Canvas API support

## Notes

- Ensure backend is running on `http://127.0.0.1:5000`
- Camera permissions required for liveness check
- Each voter can cast only one vote
