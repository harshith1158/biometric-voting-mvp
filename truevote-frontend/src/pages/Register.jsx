import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { generateProfile } from '../utils/generateProfile';
import RegistrationStepBar from '../components/RegistrationStepBar';
import { checkAadhaar } from '../services/api';

export default function Register() {
  const navigate = useNavigate();
  const [aadhaar, setAadhaar] = useState('');
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  const [checking, setChecking] = useState(false);

  // Ensure clean empty state on component mount
  useEffect(() => {
    setAadhaar('');
    setProfile(null);
  }, []);

  const handleAadhaarChange = (value) => {
    const cleanAadhaar = value.replace(/\D/g, '').slice(0, 12);
    setAadhaar(cleanAadhaar);
    setError('');

    if (cleanAadhaar.length === 12) {
      const data = generateProfile(cleanAadhaar);
      setProfile(data);
    } else {
      setProfile(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!/^\d{12}$/.test(aadhaar)) {
      setError('Please enter a valid 12-digit Aadhaar number.');
      return;
    }

    setChecking(true);
    try {
      const res = await checkAadhaar(aadhaar);
      if (res?.data?.registered) {
        setError(`This Aadhaar is already registered. Your EPIC ID is: ${res.data.epic_id}`);
        setChecking(false);
        return;
      }
    } catch (err) {
      // If API is down, allow through (fallback graceful)
    }
    setChecking(false);

    localStorage.setItem('tv_aadhaar', aadhaar);
    if (profile) {
      localStorage.setItem('profile', JSON.stringify(profile));
    }
    navigate('/otp');
  };

  return (
    <div className="px-4 py-10 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition duration-300 p-6 max-w-md mx-auto mt-10">
        <RegistrationStepBar current="aadhaar" />

        <p className="text-sm text-gray-300 mb-1">Secure Identity Verification</p>
        <h2 className="text-lg font-semibold text-white mb-3">Aadhaar Verification</h2>
        <p className="text-gray-300 text-sm">Enter your 12-digit Aadhaar to begin registration.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <input
            type="text"
            className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-orange-400 transition-all duration-300 ease-in-out"
            placeholder="12-digit Aadhaar"
            value={aadhaar}
            onChange={(e) => handleAadhaarChange(e.target.value)}
          />

          {profile && (
            <div className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition duration-300 p-4 mt-4">
              <img src={profile.avatar} className="w-20 h-20 rounded-full mx-auto mb-2" />

              <p className="text-gray-200">Name: {profile.name}</p>
              <p className="text-gray-200">Gender: {profile.gender}</p>
              <p className="text-gray-200">DOB: {profile.dob}</p>
              <p className="text-gray-200">State: {profile.state}</p>
              <p className="text-gray-200">Aadhaar: {profile.aadhaar_masked}</p>
              <p className="mt-2 flex items-center gap-2 text-orange-300 font-medium">
                <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="7" y="2" width="10" height="20" rx="2" />
                  <line x1="11" y1="18" x2="13" y2="18" />
                </svg>
                Registered Mobile: {profile.phone_masked}
              </p>
            </div>
          )}

          {error ? (
            <div className="rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 px-4 py-3">{error}</div>
          ) : null}

          <button
            className="bg-gradient-to-r from-orange-500 to-green-500 text-white px-5 py-2 rounded-lg font-semibold hover:scale-105 transition shadow-lg hover:shadow-orange-500/30 w-full disabled:opacity-60 disabled:cursor-not-allowed"
            type="submit"
            disabled={checking}
          >
            {checking ? 'Checking...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
}
