import axios from 'axios';

const TAMPER_ALERTS_KEY = 'tv_tamper_alerts';

function readTamperAlerts() {
  const raw = localStorage.getItem(TAMPER_ALERTS_KEY) || '0';
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
}

function incrementTamperAlerts() {
  const nextValue = readTamperAlerts() + 1;
  localStorage.setItem(TAMPER_ALERTS_KEY, String(nextValue));
}

export function getTamperAlertsCount() {
  return readTamperAlerts();
}

const API = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Add error interceptor for debugging
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const requestUrl = String(error?.config?.url || '');
      const responseMessage = String(error?.response?.data?.error || '').toLowerCase();
      const suspiciousVoteAttempt =
        requestUrl.includes('/cast_vote') &&
        (
          responseMessage.includes('already voted') ||
          responseMessage.includes('fingerprint already registered') ||
          responseMessage.includes('candidate not found') ||
          responseMessage.includes('epic not found')
        );

      if (suspiciousVoteAttempt) {
        incrementTamperAlerts();
      }

      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config.url,
      });
    } else if (error.request) {
      console.error('Network Error - No response:', error.message);
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Register voter
export const registerVoter = (data) => API.post('/register', data);

// Request OTP
export const requestOtp = (data) => API.post('/auth/request-otp', data);

// Verify OTP
export const verifyOtp = (data) => API.post('/auth/verify-otp', data);

// Get eKYC data
export const getEKYC = (aadhaar) => API.post('/ekyc', { aadhaar });

// Register voter with eKYC
export const registerVoterWithEKYC = (data) => API.post('/register_voter', data);

// Liveness detection
export const checkLiveness = (formData) => 
  API.post('/biometrics/selfie', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

// Fingerprint capture must always come from live RD service.
export const captureFingerprint = (data = {}) => API.post('/fingerprint/capture', data);

// Enroll fingerprint at registration
export const enrollFingerprint = (data) => API.post('/register/enroll-fingerprint', data);

// Research-only dataset fingerprint comparison (admin diagnostics)
export const compareDatasetFingerprints = (data) => API.post('/fingerprint/dataset-compare', data);

// UI simulation fingerprint verification
export const verifyFingerprintSim = (data) => API.post('/fingerprint/verify', data);

// Get voter's deterministically assigned fingerprint image name
export const getMyFingerprintImage = (epicId) => API.get(`/fingerprint/my-image?epic_id=${epicId}`);
export const listFingerprintImages = () => API.get('/fingerprint/images');

// Get candidates
export const getCandidates = () => API.get('/candidates');

// Cast vote
export const castVote = (data) => API.post('/cast_vote', data);

// Get chain status
export const getChainStatus = () => API.get('/chain_status');

// Check if Aadhaar is already registered
export const checkAadhaar = (aadhaar) => API.post('/check_aadhaar', { aadhaar });

// Validate EPIC ID at booth login
export const voterLookup = (epic_id) => API.get(`/voter_lookup?epic_id=${encodeURIComponent(epic_id)}`);

export default API;
