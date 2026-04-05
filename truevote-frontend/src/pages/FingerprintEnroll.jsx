import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { captureFingerprint, enrollFingerprint } from '../services/api';
import RegistrationStepBar from '../components/RegistrationStepBar';

export default function FingerprintEnroll() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [enrolled, setEnrolled] = useState(false);

  const epicId = localStorage.getItem('tv_epic') || '';

  const handleEnroll = async () => {
    if (!epicId) {
      setError('Voter ID missing. Please complete registration first.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Step 1: capture fingerprint from RD Service / mock
      const capRes = await captureFingerprint();
      const fingerprintHash = capRes?.data?.fingerprint_hash;

      if (!fingerprintHash) {
        throw new Error('Fingerprint hash not returned.');
      }

      // Step 2: store hash against this voter
      await enrollFingerprint({ epic_id: epicId, fingerprint_hash: fingerprintHash });

      localStorage.setItem('tv_fp_enrolled', 'true');
      setEnrolled(true);

      setTimeout(() => navigate('/success'), 1500);
    } catch (err) {
      const isNetworkFailure = !err?.response;
      const msg = isNetworkFailure
        ? 'Cannot reach backend right now. Please wait 5 seconds and try again.'
        : (err?.response?.data?.error || err?.message || 'Fingerprint enrollment failed.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-4 py-10 transition-all duration-300 ease-in-out">
      {enrolled && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/60 z-50">
          <div className="bg-white text-black p-8 rounded-xl text-center animate-scaleIn shadow-2xl">
            <div className="text-4xl text-green-600 mb-3">✅</div>
            <h2 className="text-xl font-bold">Fingerprint Enrolled</h2>
            <p className="text-sm text-gray-600 mt-2">Biometric stored. Proceeding to completion.</p>
          </div>
        </div>
      )}

      <div className="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 p-6 rounded-xl mx-auto mt-10 hover:scale-[1.02]">
        <RegistrationStepBar current="fingerprint" />

        <p className="text-sm text-gray-300 mb-1">Biometric Enrollment</p>
        <h2 className="text-lg font-semibold text-white mb-3">Fingerprint Registration</h2>
        <p className="text-sm text-gray-400 mb-6">
          Place your <span className="text-white font-medium">right index finger</span> on the scanner and press the button below. This fingerprint will be used to verify your identity at the voting booth.
        </p>

        {/* Fingerprint icon */}
        <div className="flex justify-center mb-6">
          <div className={`w-24 h-24 rounded-full flex items-center justify-center border-4 transition-all duration-300 ${loading ? 'border-yellow-400 animate-pulse' : enrolled ? 'border-green-500' : 'border-white/30'}`}>
            <svg viewBox="0 0 64 64" className="w-12 h-12 text-white/70" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M32 6C18.7 6 8 16.7 8 30c0 8 4 13 4 13" strokeLinecap="round"/>
              <path d="M32 6c13.3 0 24 10.7 24 24 0 8-4 13-4 13" strokeLinecap="round"/>
              <path d="M20 24c0-6.6 5.4-12 12-12s12 5.4 12 12c0 10-5 18-5 18" strokeLinecap="round"/>
              <path d="M44 24c0 10-12 24-12 24S20 34 20 24" strokeLinecap="round"/>
              <path d="M32 18c3.3 0 6 2.7 6 6 0 6-6 14-6 14s-6-8-6-14c0-3.3 2.7-6 6-6z" strokeLinecap="round"/>
            </svg>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 px-4 py-3 mb-4 text-sm">
            {error}
          </div>
        )}

        {enrolled ? (
          <div className="rounded-lg border border-green-500/40 bg-green-500/10 text-green-300 px-4 py-3 flex items-center gap-2 mb-4">
            <span className="check-pop inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-600 text-white">✓</span>
            Fingerprint enrolled successfully
          </div>
        ) : null}

        <button
          type="button"
          onClick={handleEnroll}
          disabled={loading || enrolled}
          className="bg-gradient-to-r from-orange-500 to-green-500 text-white px-8 py-3 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:scale-105 w-full disabled:opacity-60"
        >
          {loading ? 'Scanning...' : enrolled ? 'Enrolled ✓' : 'Scan Fingerprint'}
        </button>

        {loading && (
          <div className="flex justify-center mt-4">
            <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
}
