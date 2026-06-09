import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { requestOtp, verifyOtp } from '../services/api';
import RegistrationStepBar from '../components/RegistrationStepBar';

export default function OTP() {
  const navigate = useNavigate();
  const [otpDigits, setOtpDigits] = useState(Array(6).fill(''));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [maskedPhone, setMaskedPhone] = useState('');
  const [resendTimer, setResendTimer] = useState(30);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [shakeOtp, setShakeOtp] = useState(false);
  const [verified, setVerified] = useState(false);
  const [demoOtp, setDemoOtp] = useState('');

  const aadhaar = localStorage.getItem('tv_aadhaar') || '';
  const inputRefs = useRef([]);

  const otp = useMemo(() => otpDigits.join(''), [otpDigits]);

  // Read phone from stored profile (set by Register.jsx from DB)
  const storedProfile = (() => {
    try { return JSON.parse(localStorage.getItem('profile') || '{}'); } catch { return {}; }
  })();
  const storedPhone = storedProfile.phone || '';
  const fallbackMaskedPhone = storedPhone
    ? `${storedPhone.slice(0, 3)}****${storedPhone.slice(-2)}`
    : 'XXXXXX0000';

  useEffect(() => {
    if (!aadhaar || !/^\d{12}$/.test(aadhaar)) {
      setError('Aadhaar not found. Please start from Register page.');
      return;
    }
    void sendOtp();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aadhaar]);

  useEffect(() => {
    if (resendTimer <= 0) {
      return undefined;
    }

    const timer = setInterval(() => {
      setResendTimer((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [resendTimer]);

  const sendOtp = async () => {
    setSendingOtp(true);
    setError('');

    try {
      const response = await requestOtp({ aadhaar });
      const phoneFromApi = response?.data?.phone || '';

      setMaskedPhone(phoneFromApi || fallbackMaskedPhone);
      setDemoOtp(response?.data?.otp || '');
      setResendTimer(30);
      setOtpDigits(Array(6).fill(''));
      setVerified(false);
      setTimeout(() => inputRefs.current[0]?.focus(), 0);
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to send OTP.');
    } finally {
      setSendingOtp(false);
    }
  };

  const triggerOtpShake = () => {
    setShakeOtp(true);
    setTimeout(() => setShakeOtp(false), 350);
  };

  const handleDigitChange = (index, value) => {
    const nextValue = value.replace(/\D/g, '').slice(-1);
    const nextDigits = [...otpDigits];
    nextDigits[index] = nextValue;
    setOtpDigits(nextDigits);

    if (nextValue && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleDigitKeyDown = (index, event) => {
    if (event.key === 'Backspace' && !otpDigits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleDigitPaste = (event) => {
    event.preventDefault();
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) {
      return;
    }

    const nextDigits = Array(6).fill('');
    pasted.split('').forEach((char, idx) => {
      nextDigits[idx] = char;
    });
    setOtpDigits(nextDigits);

    const focusIndex = Math.min(pasted.length, 5);
    setTimeout(() => inputRefs.current[focusIndex]?.focus(), 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setVerified(false);

    if (!/^\d{6}$/.test(otp)) {
      setError('Enter a valid 6-digit OTP.');
      triggerOtpShake();
      return;
    }

    if (!aadhaar) {
      setError('Aadhaar not found. Please start from Register page.');
      return;
    }

    setLoading(true);

    try {
      const verifyResponse = await verifyOtp({
        aadhaar,
        otp,
      });

      if (!verifyResponse?.data?.verified) {
        throw new Error('Invalid OTP');
      }

      setVerified(true);

      // Real-user mode: voter already exists in DB.
      // epic_id and voter_id were stored by Register.jsx from checkAadhaar.
      const epicId = localStorage.getItem('tv_real_epic') || localStorage.getItem('tv_epic');
      const voterId = localStorage.getItem('tv_voter_id');

      if (!epicId) {
        throw new Error('EPIC not found. Please start from the Register page.');
      }

      localStorage.setItem('tv_epic', epicId);

      setTimeout(() => navigate('/liveness'), 700);
    } catch (err) {
      setError(err?.response?.data?.error || err?.message || 'Verification failed.');
      triggerOtpShake();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-4 py-10 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="w-full max-w-md bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 p-6 rounded-xl mx-auto mt-10 hover:scale-[1.02]">
        <RegistrationStepBar current="otp" />

        <p className="text-sm text-gray-300 mb-1">Two-Factor Authentication (OTP Verification)</p>
        <h2 className="text-lg font-semibold text-white mb-3">Aadhaar Verification</h2>
        <p className="text-sm text-gray-300 mt-2">Aadhaar: {aadhaar || 'N/A'}</p>
        <p className="text-sm text-orange-300 mt-2 flex items-center gap-2 font-medium">
          <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="7" y="2" width="10" height="20" rx="2" />
            <line x1="11" y1="18" x2="13" y2="18" />
          </svg>
          Registered Mobile: {maskedPhone || fallbackMaskedPhone}
        </p>

        {demoOtp && (
          <div className="mt-3 rounded-lg border border-yellow-400/50 bg-yellow-500/10 text-yellow-300 px-4 py-2 text-sm flex items-center gap-2">
            <span className="text-base">🔑</span>
            <span><span className="font-semibold">Demo OTP:</span> {demoOtp}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-3">
          <div className="flex items-center gap-2 text-slate-300 text-sm">
            <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="4" y="11" width="16" height="10" rx="2" />
              <path d="M8 11V7a4 4 0 0 1 8 0v4" />
            </svg>
            Enter OTP
          </div>

          <div
            className={[
              'flex justify-between gap-2 transition-all duration-300 ease-in-out',
              shakeOtp ? 'otp-shake' : '',
            ].join(' ')}
            onPaste={handleDigitPaste}
          >
            {otpDigits.map((digit, index) => (
              <input
                key={index}
                ref={(el) => {
                  inputRefs.current[index] = el;
                }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                className="w-12 h-14 border border-white/20 bg-white/10 text-white rounded-xl text-center text-2xl font-semibold focus:outline-none focus:ring-2 focus:ring-green-400 focus:shadow-[0_0_14px_rgba(22,163,74,0.35)] transition-all duration-300 ease-in-out"
                value={digit}
                onChange={(event) => handleDigitChange(index, event.target.value)}
                onKeyDown={(event) => handleDigitKeyDown(index, event)}
              />
            ))}
          </div>

          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-slate-400">
              {resendTimer > 0 ? `Resend OTP in ${resendTimer}s` : 'You can request a new OTP now'}
            </p>
            <button
              type="button"
              className="text-sm font-semibold text-orange-300 disabled:text-slate-500 transition-all duration-300 ease-in-out"
              onClick={sendOtp}
              disabled={resendTimer > 0 || sendingOtp || loading}
            >
              {sendingOtp ? 'Sending...' : 'Resend OTP'}
            </button>
          </div>

          {error ? (
            <div className="rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 px-4 py-3">{error}</div>
          ) : null}

          {verified ? (
            <div className="rounded-lg border border-green-500/40 bg-green-500/10 text-green-300 px-4 py-3 flex items-center gap-2">
              <span className="check-pop inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-600 text-white">
                ✓
              </span>
              Verified successfully
            </div>
          ) : null}

          <button
            type="submit"
            className="bg-gradient-to-r from-orange-500 to-green-500 text-white px-8 py-3 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:scale-105 w-full"
            disabled={loading || sendingOtp}
          >
            {loading ? 'Submitting...' : 'Verify OTP'}
          </button>

          {loading && (
            <div className="flex justify-center mt-4">
              <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
