import axios from "axios";

const host = typeof window !== "undefined" ? window.location.hostname : "127.0.0.1";
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || `http://${host}:5000/api`;

const API = axios.create({
  baseURL: apiBaseUrl,
});

export const registerVoter = (aadharNumber) =>
  API.post("/register", { aadhar_number: aadharNumber });

export const submitLivenessFrames = (formData) =>
  API.post("/biometrics/selfie", formData);

export default API;
