import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:5000/api',  // ✅ Use localhost to match frontend origin
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default API;