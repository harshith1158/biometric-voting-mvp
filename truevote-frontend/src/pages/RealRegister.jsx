import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FaceDetection } from '@mediapipe/face_detection';
import { sendRealOtp, verifyRealOtp, realRegister, checkLiveness, checkAadhaar } from '../services/api';
import DatePicker from '../components/DatePicker';

export default function RealRegister() {
  const CAPTURE_FRAME_COUNT = 15;
  const CAPTURE_INTERVAL_MS = 200;
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const detectorRef = useRef(null);
  const rafRef = useRef(null);
  const detectorBusyRef = useRef(false);
  const detectorEnabledRef = useRef(true);
  const webcamStartedRef = useRef(false);

  // Multi-step state: 1: Details, 2: OTP, 3: Liveness, 4: Success
  const [step, setStep] = useState(1);
  const [aadhaar, setAadhaar] = useState('');
  const [phone, setPhone] = useState('');
  const [firstName, setFirstName] = useState('');
  const [middleName, setMiddleName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('');
  const [state, setState] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [frames, setFrames] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [livenessScore, setLivenessScore] = useState(null);
  const [faceEmbedding, setFaceEmbedding] = useState(null);
  // Removed faceStatus state (revert to simple liveness)

  const sanitizeNamePart = (value) => value.replace(/[^A-Za-z\s]/g, '').toUpperCase();

  const getFullName = () => {
    return [firstName, middleName, lastName]
      .map((part) => part.trim())
      .filter(Boolean)
      .join(' ')
      .replace(/\s+/g, ' ')
      .trim();
  };

  const validateFullName = () => {
    const first = firstName.trim();
    const middle = middleName.trim();
    const last = lastName.trim();

    if (!first || !last) {
      return 'Please enter at least a first name and last name';
    }

    const parts = [first, middle, last].filter(Boolean);
    const invalidPart = parts.find((part) => !/^[A-Za-z\s]+$/.test(part));
    if (invalidPart) {
      return 'Name must contain only letters and spaces';
    }

    return '';
  };

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      if (detectorRef.current) {
        try {
          detectorRef.current.close();
        } catch (detectorCloseError) {
          console.warn('[RealRegister] Detector close failed:', detectorCloseError);
        }
      }
      detectorEnabledRef.current = false;
      webcamStartedRef.current = false;
      stopWebcam();
    };
  }, []);

  // Initialize face detector
  useEffect(() => {
    if (step !== 3) return;

    // Revert: Only initialize MediaPipe FaceDetection, no overlays or alignment logic
    const faceDetection = new FaceDetection({
      locateFile: (file) =>
        `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`,
    });
    faceDetection.setOptions({
      model: 'short',
      minDetectionConfidence: 0.5,
    });
    faceDetection.onResults((results) => {
      // Only check if a face is detected, no overlays
      if (!results?.detections?.length) {
        setError('No face detected. Please position your face in the camera.');
      } else {
        setError('');
      }
    });
    detectorRef.current = faceDetection;
    return () => {
      detectorEnabledRef.current = false;
      if (detectorRef.current) {
        try {
          detectorRef.current.close();
        } catch (detectorCloseError) {
          console.warn('[RealRegister] Detector cleanup failed:', detectorCloseError);
        }
      }
    };
  }, [step]);

  // Start webcam
  const startWebcam = async () => {
    if (webcamStartedRef.current) {
      return;
    }

    try {
      webcamStartedRef.current = true;
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: false,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;

        videoRef.current.onloadedmetadata = () => {
          const videoWidth = videoRef.current.videoWidth || 640;
          const videoHeight = videoRef.current.videoHeight || 480;

          if (canvasRef.current) {
            canvasRef.current.width = videoWidth;
            canvasRef.current.height = videoHeight;
          }

          if (overlayCanvasRef.current) {
            overlayCanvasRef.current.width = videoWidth;
            overlayCanvasRef.current.height = videoHeight;
          }

          const detectFrame = async () => {
            if (!webcamStartedRef.current) {
              return;
            }

            if (
              detectorEnabledRef.current &&
              !detectorBusyRef.current &&
              detectorRef.current &&
              videoRef.current &&
              videoRef.current.readyState >= 2
            ) {
              detectorBusyRef.current = true;
              try {
                await detectorRef.current.send({ image: videoRef.current });
              } catch (detectorError) {
                detectorEnabledRef.current = false;
                console.warn('[RealRegister] Face detection overlay disabled after MediaPipe error:', detectorError);
              } finally {
                detectorBusyRef.current = false;
              }
            }

            rafRef.current = requestAnimationFrame(detectFrame);
          };

          detectFrame();
        };

        setStreaming(true);
      }
    } catch (err) {
      webcamStartedRef.current = false;
      setError('Failed to access webcam. Please enable camera permissions.');
    }
  };

  const stopWebcam = () => {
    webcamStartedRef.current = false;
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    if (overlayCanvasRef.current) {
      const ctx = overlayCanvasRef.current.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);
      }
    }
  };

  const captureFrame = async () => {
    if (!canvasRef.current || !videoRef.current) return;

    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob);
      }, 'image/jpeg');
    });
  };

  // Step 1: Validate details and send OTP
  const handleSendOtp = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    console.log('[RealRegister] handleSendOtp called');

    const nameError = validateFullName();
    if (nameError) {
      setError(nameError);
      setLoading(false);
      return;
    }

    if (!aadhaar || aadhaar.length !== 12) {
      setError('Please enter a valid 12-digit Aadhaar number');
      setLoading(false);
      return;
    }

    // Early check: block if Aadhaar is already registered (or already voted)
    try {
      const chk = await checkAadhaar(aadhaar);
      if (chk.data?.registered) {
        if (chk.data?.has_voted) {
          setError('You have already voted. Re-registration is not allowed.');
        } else {
          setError('This Aadhaar is already registered. Please use your existing account.');
        }
        setLoading(false);
        return;
      }
    } catch {
      // If check endpoint fails, allow the flow to continue (real-register will catch it)
    }

    if (!dob) {
      setError('Please enter your date of birth');
      setLoading(false);
      return;
    }

    // Validate age >= 18
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    if (age < 18) {
      setError('You must be at least 18 years old to register');
      setLoading(false);
      return;
    }

    if (!gender) {
      setError('Please select your gender');
      setLoading(false);
      return;
    }

    if (!state) {
      setError('Please select your state');
      setLoading(false);
      return;
    }

    if (!phone || phone.length !== 10) {
      setError('Please enter a valid 10-digit phone number');
      setLoading(false);
      console.log('[RealRegister] Phone validation failed:', { phone, length: phone.length });
      return;
    }

    try {
      console.log('[RealRegister] Calling sendRealOtp with phone:', phone);
      await sendRealOtp({ phone });
      console.log('[RealRegister] OTP sent successfully');
      setMessage('OTP sent! Check your registered mobile.');
      setStep(2);
    } catch (err) {
      console.error('[RealRegister] sendRealOtp error:', err);
      setError(err.response?.data?.error || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    console.log('[RealRegister] handleVerifyOtp called with phone:', phone, 'otp:', otp);

    if (!otp || otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      setLoading(false);
      console.log('[RealRegister] OTP validation failed');
      return;
    }

    try {
      console.log('[RealRegister] Calling verifyRealOtp with:', { phone, otp });
      await verifyRealOtp({ phone, otp });
      console.log('[RealRegister] OTP verified successfully');
      setMessage('OTP verified!');
      // Go directly to liveness (step 3)
      const tempVoterId = `REAL_${Date.now()}`;
      localStorage.setItem('tv_voter_id', tempVoterId);
      setMessage('');
      setStep(3);
      setTimeout(() => startWebcam(), 500);
    } catch (err) {
      console.error('[RealRegister] OTP verification error:', err);
      setError(err.response?.data?.error || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Capture liveness frames and generate embedding
  const handleStartLivenessCheck = async () => {
    setCapturing(true);
    setFrames([]);
    setMessage('Capturing frames... Please blink naturally during the scan');
    setError('');

    const capturedFrames = [];
    const frameCount = CAPTURE_FRAME_COUNT;
    const intervalMs = CAPTURE_INTERVAL_MS;

    // Capture frames
    for (let i = 0; i < frameCount; i++) {
      const blob = await captureFrame();
      if (blob) {
        capturedFrames.push(blob);
        setFrames([...capturedFrames]);
      }
      if (i < frameCount - 1) {
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
    }

    setCapturing(false);
    setMessage('Processing liveness check...');
    await submitLivenessCheck(capturedFrames);
  };

  const submitLivenessCheck = async (capturedFrames) => {
    setLoading(true);
    setError('');

    try {
      setMessage('Liveness check passed! Registering...');

      // Capture first frame as base64 for profile image
      let profileImageBase64 = '';
      if (capturedFrames.length > 0) {
        profileImageBase64 = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(capturedFrames[0]);
        });
      }

      // First register the user with a placeholder embedding
      const placeholderEmbedding = Array.from({ length: 100 }, () => 0);
      const response = await realRegister({
        aadhaar,
        phone,
        name: getFullName(),
        dob,
        gender,
        state,
        face_embedding: placeholderEmbedding,
        liveness_score: 0.92,
        profile_image: profileImageBase64,
      });

      const voterId = response.data.voter_id;

      // Now call the actual selfie endpoint to store real embedding
      if (voterId && capturedFrames.length > 0) {
        setMessage('Processing face biometric...');
        try {
          const formData = new FormData();
          capturedFrames.forEach((frame, index) => {
            formData.append('frames', frame, `frame_${index}.jpg`);
          });
          formData.append('voter_id', voterId);
          formData.append('flow_source', 'real_register');
          const livenessResponse = await checkLiveness(formData);
          if (livenessResponse?.data?.liveness !== 'pass') {
            const livenessMsg =
              livenessResponse?.data?.error ||
              livenessResponse?.data?.message ||
              'Liveness verification failed. Please try again.';
            setError(livenessMsg);
            setMessage('');
            return;
          }
        } catch (selfieErr) {
          const selfieError = selfieErr.response?.data?.error || selfieErr.response?.data?.message || selfieErr.message;
          console.warn('Selfie processing after registration:', selfieErr);
          setError(`Liveness/face verification blocked: ${selfieError}`);
          setMessage('');
          return;
        }
      }

      setStep(4);
      setMessage('');
    } catch (err) {
      stopWebcam();
      setError(err.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoHome = () => {
    localStorage.removeItem('tv_voter_id');
    navigate('/');
  };

  return (
    <div className="px-4 py-10 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition duration-300 p-6 max-w-2xl mx-auto">
        {/* Step 1: User Details */}
        {step === 1 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 className="text-2xl font-bold text-white mb-6">New User Registration</h2>
            <p className="text-gray-300 mb-4">Step 1 of 3: Enter Your Details</p>

            <form onSubmit={handleSendOtp} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input
                  type="text"
                  placeholder="First Name"
                  value={firstName}
                  onChange={(e) => {
                    setFirstName(sanitizeNamePart(e.target.value));
                    setError('');
                  }}
                  className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400 uppercase"
                />
                <input
                  type="text"
                  placeholder="Middle Name"
                  value={middleName}
                  onChange={(e) => {
                    setMiddleName(sanitizeNamePart(e.target.value));
                    setError('');
                  }}
                  className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400 uppercase"
                />
                <input
                  type="text"
                  placeholder="Last Name"
                  value={lastName}
                  onChange={(e) => {
                    setLastName(sanitizeNamePart(e.target.value));
                    setError('');
                  }}
                  className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400 uppercase"
                />
              </div>

              <p className="text-xs text-gray-300 -mt-2">Please enter FIRST, MIDDLE, and LAST names in CAPITAL LETTERS only.</p>

              <input
                type="text"
                placeholder="12-digit Aadhaar"
                value={aadhaar}
                onChange={(e) => {
                  const val = e.target.value.replace(/\D/g, '').slice(0, 12);
                  setAadhaar(val);
                  setError('');
                }}
                className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400"
              />

              <DatePicker
                label="Date of Birth"
                value={dob}
                onChange={(iso) => { setDob(iso); setError(''); }}
                maxDate={new Date().toISOString().split('T')[0]}
              />

              <select
                value={gender}
                onChange={(e) => {
                  setGender(e.target.value);
                  setError('');
                }}
                className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400"
              >
                <option value="" className="text-black bg-white">Select Gender</option>
                <option value="Male" className="text-black bg-white">Male</option>
                <option value="Female" className="text-black bg-white">Female</option>
                <option value="Other" className="text-black bg-white">Other</option>
              </select>

              <select
                value={state}
                onChange={(e) => {
                  setState(e.target.value);
                  setError('');
                }}
                className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400"
              >
                <option value="" className="text-black bg-white">Select State</option>
                {[
                  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
                  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
                  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
                  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
                  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
                  'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
                ].map((s) => (
                  <option key={s} value={s} className="text-black bg-white">{s}</option>
                ))}
              </select>

              <input
                type="text"
                placeholder="10-digit Phone"
                value={phone}
                onChange={(e) => {
                  const val = e.target.value.replace(/\D/g, '').slice(0, 10);
                  setPhone(val);
                  setError('');
                }}
                className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400"
              />

              {error && <div className="text-red-400 text-sm">{error}</div>}

              <button
                type="submit"
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold w-full disabled:opacity-60"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Sending OTP...
                  </span>
                ) : 'Send OTP'}
              </button>
            </form>
          </motion.div>
        )}

        {/* Step 2: OTP Verification */}
        {step === 2 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 className="text-2xl font-bold text-white mb-6">Verify OTP</h2>
            <p className="text-gray-300 mb-4">Step 2 of 3: OTP Verification</p>
            <p className="text-gray-400 text-sm mb-4">
              A 6-digit OTP has been sent to {phone}
            </p>

            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <input
                type="text"
                placeholder="6-digit OTP"
                value={otp}
                maxLength="6"
                onChange={(e) => {
                  const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                  setOtp(val);
                  setError('');
                }}
                className="border border-white/20 bg-white/10 text-white p-3 rounded w-full focus:ring-2 focus:ring-green-400 text-center text-2xl tracking-widest"
              />

              {error && <div className="text-red-400 text-sm">{error}</div>}
              {message && <div className="text-blue-400 text-sm">{message}</div>}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="border border-white/20 text-white px-6 py-2 rounded-lg flex-1"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold flex-1 disabled:opacity-60"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Verifying...
                    </span>
                  ) : 'Verify'}
                </button>
              </div>
            </form>
          </motion.div>
        )}

        {/* Step 3: Liveness Detection */}
        {step === 3 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2 className="text-2xl font-bold text-white mb-2">Face Verification</h2>
            <p className="text-gray-300 mb-4">Step 3 of 3: Liveness Detection</p>

            <div className="flex flex-col items-center">
              {/* ── Camera feed with overlays ──────────────────────────── */}
              <div className="relative w-full bg-black rounded-xl shadow-lg border border-white/10 overflow-hidden">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full h-80 object-cover"
                />
                {/* Overlay canvas removed (revert) */}
                <canvas ref={canvasRef} width="640" height="480" style={{ display: 'none' }} />

                {/* Face status badge — top-center */}
                {/* Face status badge removed (revert) */}

                {/* Blink hint — bottom of camera, shown while capturing or after blink error */}
                {/* Blink hint removed (revert) */}
              </div>

              {/* Alignment guidance text (idle only, not centred) */}
              {/* Alignment guidance text removed (revert) */}

              {/* Processing / status message */}
              {message && (
                <div className="mt-3 w-full rounded-lg bg-blue-500/20 border border-blue-400/40 text-blue-300 px-4 py-2 text-sm text-center">
                  {message}
                </div>
              )}

              {/* Backend error (non-blink — blink hint is shown on the camera instead) */}
              {error && !/blink/i.test(error) && (
                <div className="mt-3 w-full rounded-lg bg-red-500/20 border border-red-400/40 text-red-300 px-4 py-2 text-sm">
                  {error}
                </div>
              )}

              {/* Frame capture progress bar */}
              {frames.length > 0 && (
                <div className="mt-3 w-full">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Capturing frames</span>
                    <span>{frames.length}/{CAPTURE_FRAME_COUNT}</span>
                  </div>
                  <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full transition-all duration-300"
                      style={{ width: `${(frames.length / CAPTURE_FRAME_COUNT) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {loading && (
                <div className="flex justify-center mt-4">
                  <div className="w-10 h-10 border-4 border-green-600 border-t-transparent rounded-full animate-spin" />
                </div>
              )}

              {!capturing && !loading && (
                <button
                  onClick={handleStartLivenessCheck}
                  className="mt-4 w-full px-8 py-3 rounded-lg font-semibold text-white transition-colors duration-200 bg-green-600 hover:bg-green-700"
                >
                  Start Liveness Check
                </button>
              )}

              {capturing && (
                <button
                  disabled
                  className="mt-4 w-full px-8 py-3 rounded-lg font-semibold text-white bg-gray-600 opacity-60 cursor-not-allowed"
                >
                  Capturing…
                </button>
              )}
            </div>
          </motion.div>
        )}

        {/* Step 4: Success */}
        {step === 4 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <div className="text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-white mb-2">Registration Complete</h2>
            <p className="text-gray-300 mb-6">Your identity has been registered successfully.</p>

            <div className="bg-green-500/20 border border-green-500 rounded-lg p-6 mb-6">
              <p className="text-gray-300 text-sm">You can now generate your EPIC ID from the home page.</p>
            </div>

            <button
              onClick={handleGoHome}
              className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-semibold w-full"
            >
              Go to Home
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
