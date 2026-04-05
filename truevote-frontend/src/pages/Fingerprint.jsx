import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { verifyFingerprintSim, getMyFingerprintImage, listFingerprintImages } from '../services/api';
import { playSuccessSound } from '../utils/soundHelpers';

export default function Fingerprint() {
  const navigate = useNavigate();
  const [fpImages, setFpImages] = useState([]);
  const [selectedFP, setSelectedFP] = useState('');
  const [registeredImage, setRegisteredImage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [fpSuccess, setFpSuccess] = useState(false);
  const epicId = localStorage.getItem('tv_epic') || '';

  useEffect(() => {
    if (localStorage.getItem('tv_verified') !== 'true') {
      navigate('/verify');
    }
  }, [navigate]);

  useEffect(() => {
    if (!epicId) return;
    getMyFingerprintImage(epicId)
      .then((res) => setRegisteredImage(res?.data?.image ?? ''))
      .catch(() => {});
  }, [epicId]);

  useEffect(() => {
    listFingerprintImages()
      .then((res) => setFpImages(res?.data?.images ?? []))
      .catch(() => {});
  }, []);

  const displayList = fpImages.length
    ? (registeredImage && !fpImages.includes(registeredImage)
        ? [registeredImage, ...fpImages]
        : fpImages)
    : (registeredImage ? [registeredImage] : []);

  const handleScan = async () => {
    if (!epicId) {
      setError('EPIC not found. Please start from booth login.');
      return;
    }
    if (!selectedFP) {
      setError('Please select a fingerprint from the list.');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      // Add delay for cinematic effect (1.5s animation)
      await new Promise(res => setTimeout(res, 1500));
      
      const res = await verifyFingerprintSim({ epic_id: epicId, fingerprint_id: selectedFP });
      const data = res?.data ?? {};
      setResult({
        score: data.score ?? 0,
        status: data.status ?? 'pass',
        message: data.message ?? '',
        fingerprint_id: data.fingerprint_id ?? '',
        selected: selectedFP,
      });

      if (data.status === 'pass') {
        playSuccessSound();
        setFpSuccess(true);
        window.setTimeout(() => {
          setFpSuccess(false);
          navigate('/booth-voting');
        }, 2000);
      }
    } catch (err) {
      const errData = err?.response?.data ?? {};
      setResult({
        score: 0,
        status: 'fail',
        message: errData.error ?? 'Verification failed.',
        assigned: errData.assigned ?? '',
        selected: errData.selected ?? selectedFP,
      });
      setError(errData.error ?? 'Verification failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-4 py-10 transition-all duration-300 ease-in-out">
      {fpSuccess && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/60 z-50">
          <div className="bg-white text-black p-8 rounded-xl text-center animate-scaleIn shadow-2xl">
            <div className="text-4xl text-green-600 mb-3">✅</div>
            <h2 className="text-xl font-bold">Fingerprint Verified</h2>
            <p className="text-sm text-gray-600 mt-2">Identity confirmed. Proceeding to vote...</p>
          </div>
        </div>
      )}

      <div className="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 rounded-xl p-8 text-center mx-auto mt-10">
        <p className="text-sm text-gray-300 mb-1">Biometric Fingerprint Authentication</p>
        <h2 className="text-lg font-semibold text-white mb-6">Fingerprint Verification</h2>

        {registeredImage ? (
          <div className="mb-3 rounded-xl border border-blue-400/30 bg-blue-400/10 px-3 py-2 text-left">
            <p className="text-xs text-blue-300 font-semibold uppercase tracking-wide mb-0.5">Your Registered Fingerprint</p>
            <p className="text-sm font-bold text-white font-mono">{registeredImage}</p>
            <p className="text-xs text-gray-400 mt-0.5">Select this for a successful match.</p>
          </div>
        ) : null}

        <p className="text-xs text-gray-400 mb-3 text-left">
          Select a fingerprint image to simulate scanning. Your registered print will be matched against it.
        </p>

        <select
          value={selectedFP}
          onChange={(e) => { setSelectedFP(e.target.value); setResult(null); setError(''); }}
          className="w-full p-3 bg-gray-900 text-white border border-gray-600 rounded"
        >
          <option className="text-black bg-white" value="">Select Fingerprint</option>
          {displayList.map((fp) => (
            <option key={fp} value={fp} className="text-black bg-white">
              {fp === registeredImage ? `${fp}  ✓ Registered` : fp}
            </option>
          ))}
        </select>

        {result && (() => {
          const confidence =
            result.score > 0.7 ? { label: 'High', cls: 'text-green-300' } :
            result.score > 0.5 ? { label: 'Medium', cls: 'text-yellow-300' } :
                                 { label: 'Low', cls: 'text-orange-300' };
          return (
            <div className={`mt-4 rounded-xl border px-4 py-3 text-sm text-left transition-all ${
              result.status === 'pass'
                ? 'border-green-400/40 bg-green-400/10 text-green-200'
                : 'border-red-400/40 bg-red-400/10 text-red-200'
            }`}>
              <p className="font-bold text-base mb-2">
                {result.status === 'pass' ? 'âœ” Fingerprint ID Matched' : 'âœ– Identity Mismatch'}
              </p>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs mb-2 font-mono">
                <span className="text-gray-400">Selected ID</span>
                <span className="text-white">{result.selected || selectedFP}</span>
                <span className="text-gray-400">Assigned ID</span>
                <span className="text-white">{result.fingerprint_id || result.assigned || 'â€”'}</span>
              </div>
              {result.status === 'pass' && (
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-gray-300">Score: <span className="font-bold text-white">{result.score}</span></span>
                  <span className={`font-semibold ${confidence.cls}`}>Confidence: {confidence.label}</span>
                </div>
              )}
              {result.status !== 'pass' && (
                <p className="text-xs mt-1 text-red-300">
                  Selected fingerprint does not match your registered identity.
                </p>
              )}
            </div>
          );
        })()}

        {error ? (
          <div className="mt-2 mb-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 px-4 py-3 text-left text-sm">
            {error}
          </div>
        ) : null}

        <button
          className="w-full px-8 py-3 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:scale-105 mt-4 text-white font-semibold bg-gradient-to-r from-orange-500 to-green-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:scale-100"
          onClick={handleScan}
          disabled={loading || !selectedFP}
        >
          {loading ? 'Verifying...' : 'Scan Fingerprint'}
        </button>

        {loading && (
          <div className="relative w-40 h-40 mx-auto mt-6 flex flex-col items-center justify-center">
            {/* Outer pulsing ring */}
            <div className="absolute inset-0 border-2 border-green-500 rounded-full animate-pulse" />
            
            {/* Middle rotating ring */}
            <div className="absolute inset-0 border-2 border-transparent border-t-green-400 border-r-green-400 rounded-full animate-spin" style={{ animationDuration: '2s' }} />
            
            {/* Inner pinging ring */}
            <div className="absolute inset-4 bg-green-500 opacity-20 animate-ping rounded-full" />
            
            {/* Center scanner text */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-green-400 text-sm font-bold animate-pulse">Scanning...</div>
                <div className="text-green-300/60 text-xs mt-1">Processing fingerprint</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
