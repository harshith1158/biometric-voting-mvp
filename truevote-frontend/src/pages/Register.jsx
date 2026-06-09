import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
    setProfile(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!/^\d{12}$/.test(aadhaar)) {
      setError('Please enter a valid 12-digit Aadhaar number.');
      return;
    }

    // If profile already loaded, proceed to liveness
    if (profile) {
      navigate('/liveness');
      return;
    }

    setChecking(true);
    try {
      const res = await checkAadhaar(aadhaar);
      if (res?.data?.registered) {
        // User exists in DB — store real data and show profile
        localStorage.setItem('tv_is_real_user', 'true');
        localStorage.setItem('tv_real_epic', res.data.epic_id);
        localStorage.setItem('tv_epic', res.data.epic_id);
        if (res.data.voter_id) {
          localStorage.setItem('tv_voter_id', res.data.voter_id);
        }
        if (res.data.profile) {
          localStorage.setItem('profile', JSON.stringify(res.data.profile));
          setProfile(res.data.profile);
        }
        localStorage.setItem('tv_aadhaar', aadhaar);
      } else {
        // User NOT in DB — block
        setError('User not registered. Please register first.');
        setChecking(false);
        return;
      }
    } catch (err) {
      setError(err?.response?.data?.error || 'Unable to verify Aadhaar. Please try again.');
      setChecking(false);
      return;
    }
    setChecking(false);
  };

  return (
    <div className="px-4 py-10 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition duration-300 p-6 max-w-md mx-auto mt-10">
        <RegistrationStepBar current="aadhaar" />

        <p className="text-sm text-gray-300 mb-1">Secure Identity Verification</p>
        <h2 className="text-lg font-semibold text-white mb-3">Generate EPIC ID</h2>
        <p className="text-gray-300 text-sm">Enter your 12-digit Aadhaar to generate your EPIC ID.</p>

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
              {profile.profile_image && (
                <img src={profile.profile_image} className="w-20 h-20 rounded-full mx-auto mb-3 object-cover" alt="Profile" />
              )}
              <p className="text-gray-200">Name: {profile.name}</p>
              <p className="text-gray-200">Gender: {profile.gender}</p>
              <p className="text-gray-200">DOB: {profile.dob}</p>
              <p className="text-gray-200">State: {profile.state}</p>
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
            {checking ? 'Checking...' : profile ? 'Proceed to Face Verification →' : 'Verify Aadhaar'}
          </button>


        </form>
      </div>
    </div>
  );
}
