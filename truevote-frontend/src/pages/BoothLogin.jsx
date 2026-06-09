import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { voterLookup } from '../services/api';

export default function BoothLogin() {
  const navigate = useNavigate();
  const [epic, setEpic] = useState('');
  const [error, setError] = useState('');
  const [checking, setChecking] = useState(false);

  // Ensure clean empty state on component mount
  useEffect(() => {
    setEpic('');
  }, []);

  const handleVerify = async (e) => {
    e.preventDefault();
    const trimmed = epic.trim();
    if (!trimmed) return;
    setError('');
    setChecking(true);

    try {
      const res = await voterLookup(trimmed);
      // Valid EPIC — store profile and proceed
      localStorage.setItem('tv_epic', trimmed);
      if (res?.data?.profile) {
        localStorage.setItem('profile', JSON.stringify(res.data.profile));
      }
      localStorage.removeItem('tv_verified');
      localStorage.removeItem('tv_vote_result');
      navigate('/verify');
    } catch (err) {
      const msg = err?.response?.data?.error;
      if (err?.response?.status === 404) {
        setError('Invalid EPIC ID. No voter found with this ID.');
      } else if (err?.response?.status === 400) {
        setError(msg || 'This voter has already cast their vote.');
      } else {
        // API down — allow through gracefully
        localStorage.setItem('tv_epic', trimmed);
        localStorage.removeItem('tv_verified');
        localStorage.removeItem('tv_vote_result');
        navigate('/verify');
      }
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="px-4 py-10 transition-all duration-300 ease-in-out">
      <div className="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 p-6 rounded-xl mx-auto mt-10 hover:scale-[1.02]">
        <p className="text-sm text-gray-300 mb-1">Polling Station Access</p>
        <h2 className="text-lg font-semibold text-white mb-3">Booth Login</h2>
        <form onSubmit={handleVerify} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-2">EPIC ID</label>
            <input
              type="text"
              value={epic}
              onChange={(e) => { setEpic(e.target.value); setError(''); }}
              className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400 transition-all duration-300 ease-in-out"
              placeholder="Enter EPIC ID"
            />
          </div>
          {error && (
            <div className="rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 px-4 py-3 text-sm">{error}</div>
          )}
          <button
            type="submit"
            disabled={checking}
            className="bg-gradient-to-r from-orange-500 to-green-500 text-white px-8 py-3 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:scale-105 w-full disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {checking ? 'Verifying...' : 'Verify'}
          </button>
        </form>
      </div>
    </div>
  );
}
