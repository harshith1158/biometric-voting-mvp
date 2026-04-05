import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function VerifyVoter() {
  const navigate = useNavigate();
  const [verified, setVerified] = useState(false);
  const epic = localStorage.getItem('tv_epic') || 'N/A';

  const profile = useMemo(() => {
    const localProfile = localStorage.getItem('profile');
    if (localProfile) {
      return JSON.parse(localProfile);
    }

    const fallbackProfile = localStorage.getItem('tv_profile');
    if (fallbackProfile) {
      return JSON.parse(fallbackProfile);
    }

    return null;
  }, []);

  if (!profile) {
    return (
      <div className="text-center mt-10 px-4">
        <p className="text-gray-300">No voter found. Please enter your EPIC ID at the booth.</p>
      </div>
    );
  }

  const handleConfirm = () => {
    setVerified(true);
    localStorage.setItem('tv_verified', 'true');
    navigate('/booth-voting');
  };

  return (
    <div className="text-center mt-10 px-4 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 p-6 rounded-xl max-w-md mx-auto">
        <p className="text-sm text-gray-300 mb-2">Identity Confirmation at Booth</p>
        <img src={profile.avatar} className="w-24 h-24 rounded-full mx-auto" />

        <h2 className="text-xl font-bold mt-2 text-white">{profile.name}</h2>

        {/* Voter details */}
        <div className="mt-4 text-left space-y-2 bg-white/5 rounded-xl p-4">
          <p className="text-gray-300 text-sm"><span className="text-gray-400">Name:</span> <span className="text-white font-medium">{profile.name}</span></p>
          <p className="text-gray-300 text-sm"><span className="text-gray-400">Gender:</span> {profile.gender} | {profile.state}</p>
          <p className="text-gray-300 text-sm"><span className="text-gray-400">Aadhaar:</span> {profile.aadhaar_masked}</p>
          <p className="text-gray-300 text-sm"><span className="text-gray-400">EPIC ID:</span> <span className="font-mono text-white">{epic}</span></p>
        </div>

        {/* Inline fingerprint verified badge */}
        <div className="mt-4 p-4 bg-green-900/30 border border-green-500/40 rounded-xl text-green-300 text-sm text-left shadow-[0_0_15px_rgba(0,255,100,0.2)]">
          <p className="font-semibold text-base mb-1">✓ Fingerprint Verified</p>
          <p className="text-green-100"><span className="font-semibold text-white">{profile.name}</span>'s fingerprint has been recognized and verified using biometric fingerprint datasets!</p>
        </div>

        <button
          onClick={handleConfirm}
          className="bg-gradient-to-r from-orange-500 to-green-500 text-white px-6 py-3 mt-5 rounded-xl w-full font-semibold shadow-lg hover:scale-105 transition-all duration-300"
        >
          Confirm & Enter Booth →
        </button>

        <button
          onClick={() => window.location.href = '/'}
          className="bg-red-500/80 text-white px-4 py-2 mt-2 rounded block mx-auto"
        >
          Not You?
        </button>

        {verified ? <p className="text-xs text-emerald-400 mt-2">Verified, proceeding to fingerprint scan...</p> : null}
      </div>
    </div>
  );
}
