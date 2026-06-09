import { useState, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FaceDetection } from '@mediapipe/face_detection';
import { checkLiveness, verifyFace } from '../services/api';
import RegistrationStepBar from '../components/RegistrationStepBar';

export default function Liveness() {
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
  const [streaming, setStreaming] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [frames, setFrames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const [faceMatch, setFaceMatch] = useState(null);
  const [voterId, setVoterId] = useState(localStorage.getItem('tv_voter_id') || '');
  const [faceInstruction, setFaceInstruction] = useState('Align your face inside the frame');
  const lastInstructionRef = useRef('');
  const profile = useMemo(() => {
    const rawProfile = localStorage.getItem('profile') || localStorage.getItem('tv_profile');
    if (!rawProfile) {
      return null;
    }

    try {
      return JSON.parse(rawProfile);
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    const freshVoterId = localStorage.getItem('tv_voter_id');
    if (freshVoterId && !voterId) {
      setVoterId(freshVoterId);
      console.log('[Liveness] Loaded voter_id from localStorage:', freshVoterId);
    }

    startWebcam();

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      if (detectorRef.current) {
        try {
          detectorRef.current.close();
        } catch (detectorCloseError) {
          console.warn('[Liveness] Detector close failed:', detectorCloseError);
        }
      }
      detectorEnabledRef.current = false;
      webcamStartedRef.current = false;
      stopWebcam();
    };
  }, []);

  useEffect(() => {
    const faceDetection = new FaceDetection({
      locateFile: (file) =>
        `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`,
    });

    faceDetection.setOptions({
      model: 'short',
      minDetectionConfidence: 0.5,
    });

    faceDetection.onResults((results) => {
      const canvas = overlayCanvasRef.current;
      if (!canvas || canvas.width === 0 || canvas.height === 0) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const cw = canvas.width;
      const ch = canvas.height;
      const cx = cw / 2;
      const cy = ch / 2;
      const ovalW = cw * 0.44;
      const ovalH = ch * 0.74;

      // Determine face status and instruction
      let instruction = 'Align your face inside the frame';
      let ovalColor = 'rgba(255, 220, 80, 0.9)';

      if (results?.detections?.length > 0) {
        const box = results.detections[0].boundingBox;
        const faceW = box.width;
        const faceCX = box.xCenter;
        const faceCY = box.yCenter;

        if (faceW < 0.18) {
          instruction = 'Move closer';
          ovalColor = 'rgba(255, 165, 0, 0.9)';
        } else if (faceW > 0.62) {
          instruction = 'Move slightly back';
          ovalColor = 'rgba(255, 165, 0, 0.9)';
        } else if (Math.abs(faceCX - 0.5) > 0.14 || Math.abs(faceCY - 0.5) > 0.14) {
          instruction = 'Center your face';
          ovalColor = 'rgba(255, 200, 50, 0.9)';
        } else {
          instruction = 'Hold still — perfect!';
          ovalColor = 'rgba(80, 220, 100, 0.9)';
        }
      }

      // Update instruction state only when changed (avoids unnecessary re-renders)
      if (instruction !== lastInstructionRef.current) {
        lastInstructionRef.current = instruction;
        setFaceInstruction(instruction);
      }

      // 1. Draw semi-transparent dark overlay over full canvas
      ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
      ctx.fillRect(0, 0, cw, ch);

      // 2. Punch a clear oval hole through the overlay
      ctx.globalCompositeOperation = 'destination-out';
      ctx.beginPath();
      ctx.ellipse(cx, cy, ovalW / 2, ovalH / 2, 0, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 1)';
      ctx.fill();
      ctx.globalCompositeOperation = 'source-over';

      // 3. Draw oval guide border with glow
      ctx.strokeStyle = ovalColor;
      ctx.lineWidth = 3;
      ctx.shadowColor = ovalColor;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.ellipse(cx, cy, ovalW / 2, ovalH / 2, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.shadowBlur = 0;
    });

    detectorRef.current = faceDetection;

    return () => {
      detectorEnabledRef.current = false;
      if (detectorRef.current) {
        try {
          detectorRef.current.close();
        } catch (detectorCloseError) {
          console.warn('[Liveness] Detector cleanup failed:', detectorCloseError);
        }
      }
    };
  }, []);

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
                console.warn('[Liveness] Face detection overlay disabled after MediaPipe error:', detectorError);
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

  const handleStartLivenessCheck = async () => {
    const currentVoterId = localStorage.getItem('tv_voter_id');
    
    if (!voterId && !currentVoterId) {
      setError('Voter ID missing. Complete Aadhaar registration first.');
      console.error('[Liveness] ERROR: No voter_id in localStorage');
      return;
    }

    if (voterId !== currentVoterId) {
      setVoterId(currentVoterId);
      console.log('[Liveness] Updated voter_id from localStorage:', currentVoterId);
    }

    setCapturing(true);
    setFrames([]);
    setMessage('Capturing frames... Please blink naturally during the scan');
    setError('');

    const capturedFrames = [];
    const frameCount = CAPTURE_FRAME_COUNT;
    const intervalMs = CAPTURE_INTERVAL_MS;

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
    setFaceMatch(null);

    try {
      // Ensure we have the latest voter_id from localStorage
      const currentVoterId = localStorage.getItem('tv_voter_id');
      if (!currentVoterId) {
        console.error('[Liveness] CRITICAL: voter_id missing from localStorage!');
        setError('Voter ID not found. Please restart registration.');
        setLoading(false);
        return;
      }
      
      console.log('[Liveness] Using voter_id:', currentVoterId);
      
      const formData = new FormData();
      capturedFrames.forEach((frame, index) => {
        formData.append('frames', frame, `frame_${index}.jpg`);
      });
      formData.append('voter_id', currentVoterId);

      const response = await checkLiveness(formData);

      if (response.data.liveness === 'pass') {
        setResult({
          status: 'processing',
          message: 'Liveness captured. Verifying against your registered face...',
          earValues: response.data.ear_values,
          biometricId: response.data.biometric_id,
        });
        if (response.data.biometric_id) {
          localStorage.setItem('tv_biometric_id', String(response.data.biometric_id));
        }

        // ✅ CRITICAL: Immediately perform face verification after liveness passes
        setMessage('Liveness verified! Verifying identity...');
        console.log('[Liveness] ✓ Liveness passed - Capturing 5 frames for multi-frame face verification');

        try {
          // Capture 5 frames over ~1 second for multi-frame matching
          const liveFrames = [];
          for (let fi = 0; fi < 5; fi++) {
            const blob = await captureFrame();
            if (blob) liveFrames.push(blob);
            if (fi < 4) await new Promise((r) => setTimeout(r, 150));
          }

          if (liveFrames.length === 0) {
            console.error('[Liveness] Failed to capture any frames for face verification');
            setError('Failed to capture frames for identity verification');
            setLoading(false);
            return;
          }

          console.log(`[Liveness] Captured ${liveFrames.length} frames — calling multi-frame face verification...`);

          // Call multi-frame face verification endpoint
          const faceVerifyFormData = new FormData();
          liveFrames.forEach((frame, idx) => {
            faceVerifyFormData.append('frames', frame, `live_face_${idx}.jpg`);
          });
          faceVerifyFormData.append('voter_id', currentVoterId);
          const faceResponse = await verifyFace(faceVerifyFormData);
          
          console.log('[Liveness] Face verification response:', faceResponse.data);
          
          if (faceResponse.data.verified === true) {
            // ✅ FACE MATCH - IDENTITY CONFIRMED - Allow EPIC generation
            console.log('[Liveness] ✅ FACE IDENTITY CONFIRMED - Same person - Proceeding to EPIC');
            setResult({
              status: 'pass',
              message: 'Liveness and identity verified successfully!',
              earValues: response.data.ear_values,
              biometricId: response.data.biometric_id,
            });
            setFaceMatch({
              matched: true,
              distance: faceResponse.data.distance,
              name: profile?.name || '',
            });
            setMessage('Identity verified! Face matched. Generating EPIC ID...');
            
            // Auto-navigate after confirmation
            setTimeout(() => {
              navigate('/success');
            }, 1500);
          } else {
            // ❌ FACE MISMATCH - BLOCK - Different person detected
            console.log('[Liveness] ❌ FACE VERIFICATION FAILED - Different person detected');
            setResult({
              status: 'fail',
              message: 'Live face does not match the registered face.',
              earValues: response.data.ear_values || [],
              biometricId: response.data.biometric_id,
            });
            setFaceMatch({
              matched: false,
              distance: faceResponse.data.distance,
              name: profile?.name || '',
            });
            setError('❌ IDENTITY VERIFICATION FAILED: Face does not match. Access denied.');
            setMessage('');
            alert('Identity verification failed. The face does not match your registered face.');
            setLoading(false);
          }
        } catch (faceErr) {
          console.error('[Liveness] Face verification error:', faceErr);
          const faceError = faceErr.response?.data?.error || 'Face verification failed';
          setResult({
            status: 'fail',
            message: faceError,
            earValues: response.data.ear_values || [],
            biometricId: response.data.biometric_id,
          });
          setError(`Identity verification error: ${faceError}`);
          alert(faceError);
          setMessage('');
          setLoading(false);
        }
      } else {
        setResult({
          status: 'fail',
          message: 'Liveness check failed. Please try again.',
          earValues: response.data.ear_values || [],
        });
        setMessage('');
      }
    } catch (err) {
      const livenessError = err.response?.data?.error || err.response?.data?.message || 'Liveness failed';
      setError(livenessError);
      alert(livenessError);
      setMessage('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="py-8 px-4 transition-opacity duration-500 opacity-100 ease-in-out">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition duration-300 p-8 max-w-5xl w-full mx-auto"
      >
        <RegistrationStepBar current="liveness" />

        <p className="text-sm text-gray-300 text-center mb-1">Biometric Verification in Progress</p>
        <h2 className="text-3xl font-bold text-center text-white mb-4">
          Liveness Detection
        </h2>
        <p className="text-center text-gray-300 mb-8">
          Align your face and move slightly
        </p>

        <div className="grid gap-6 mt-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:items-start">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <p className="text-xs uppercase tracking-[0.24em] text-orange-300 mb-2">
              Registered Face
            </p>
            <h3 className="text-xl font-semibold text-white mb-4">
              Reference Image Used For Match
            </h3>

            {profile?.profile_image ? (
              <img
                src={profile.profile_image}
                alt="Registered voter"
                className="w-full aspect-[4/5] rounded-2xl object-cover border border-white/10 bg-black/30"
              />
            ) : (
              <div className="w-full aspect-[4/5] rounded-2xl border border-dashed border-white/15 bg-black/20 flex items-center justify-center text-gray-400 text-sm text-center px-6">
                Registered photo preview is unavailable, but backend matching still uses the saved registration face.
              </div>
            )}

            <div className="mt-4 space-y-2 text-sm text-gray-300">
              {profile?.name ? <p><span className="text-gray-400">Name:</span> {profile.name}</p> : null}
              {profile?.dob ? <p><span className="text-gray-400">DOB:</span> {profile.dob}</p> : null}
              {profile?.gender ? <p><span className="text-gray-400">Gender:</span> {profile.gender}</p> : null}
              {profile?.state ? <p><span className="text-gray-400">State:</span> {profile.state}</p> : null}
            </div>

            <div className="mt-4 rounded-xl border border-orange-500/30 bg-orange-500/10 px-4 py-3 text-sm text-orange-100">
              Your live camera feed is checked for liveness and then matched against this registered face before EPIC generation continues.
            </div>
          </div>

          <div className="flex flex-col items-center">
            <div className="relative bg-black rounded-xl shadow-lg border overflow-hidden w-full">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full h-96 object-cover"
              />
              <canvas
                ref={overlayCanvasRef}
                className="absolute top-0 left-0 w-full h-96 pointer-events-none"
              />
              <canvas
                ref={canvasRef}
                width="640"
                height="480"
                style={{ display: 'none' }}
              />
            </div>

            <p className={`mt-3 text-sm font-medium text-center transition-colors duration-300 ${
              faceInstruction === 'Hold still \u2014 perfect!'
                ? 'text-green-400'
                : faceInstruction === 'Align your face inside the frame'
                ? 'text-gray-300'
                : 'text-yellow-300'
            }`}>
              {faceInstruction}
            </p>

            {message && (
              <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded text-center mt-4 w-full transition-all duration-300 ease-in-out">
                {message}
              </div>
            )}

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4 w-full transition-all duration-300 ease-in-out">
                {error}
              </div>
            )}

            {result && result.status === 'pass' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-green-50 border-2 border-green-500 rounded-lg p-4 text-center mt-4 w-full"
              >
                <div className="text-4xl mb-2">✓</div>
                <p className="text-green-700 font-bold">{result.message}</p>
              </motion.div>
            )}

            {result && result.status === 'processing' && (
              <div className="bg-blue-50 border-2 border-blue-500 rounded-lg p-4 text-center mt-4 w-full">
                <p className="text-blue-700 font-bold">{result.message}</p>
              </div>
            )}

            {faceMatch && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`border-2 rounded-lg p-5 text-center mt-4 w-full ${
                  faceMatch.matched
                    ? 'bg-green-50 border-green-500'
                    : 'bg-red-50 border-red-500'
                }`}
              >
                <p className={`text-lg font-bold ${faceMatch.matched ? 'text-green-700' : 'text-red-700'}`}>
                  {faceMatch.matched ? '✓ Face Matched' : '✗ Face Mismatch'}
                </p>
                {typeof faceMatch.distance === 'number' ? (
                  <p className="text-gray-700 text-sm mt-1">
                    Match distance: <span className="font-mono font-bold text-base">{faceMatch.distance.toFixed(4)}</span>
                  </p>
                ) : null}
                {faceMatch.name ? (
                  <p className="text-gray-600 text-sm mt-1">Registered as: <span className="font-semibold">{faceMatch.name}</span></p>
                ) : null}
                {faceMatch.matched ? (
                  <p className="text-green-600 text-xs mt-2">Generating EPIC ID...</p>
                ) : (
                  <p className="text-red-600 text-xs mt-2">Registered face and live liveness capture do not match.</p>
                )}
              </motion.div>
            )}

            {result && result.status === 'fail' && (
              <div className="bg-red-50 border-2 border-red-500 rounded-lg p-4 text-center mt-4 w-full">
                <p className="text-red-700 font-bold">{result.message}</p>
                <p className="text-sm text-gray-600 mt-2">
                  EAR Values: {result.earValues.map((v) => v.toFixed(2)).join(', ')}
                </p>
              </div>
            )}

            {frames.length > 0 && (
              <div className="text-center text-sm text-gray-600 mt-4">
                Frames captured: {frames.length}/{CAPTURE_FRAME_COUNT}
              </div>
            )}

            {loading && (
              <div className="flex justify-center mt-4">
                <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              </div>
            )}

            {!result && (
              <button
                onClick={handleStartLivenessCheck}
                disabled={capturing || loading || !streaming}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:scale-105 mt-4 w-full"
              >
                {capturing ? 'Capturing...' : loading ? 'Processing...' : 'Verify'}
              </button>
            )}

            {result && result.status === 'fail' && (
              <button
                onClick={() => {
                  setFrames([]);
                  setResult(null);
                  setFaceMatch(null);
                  setMessage('');
                  setError('');
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:scale-105 mt-4 w-full"
              >
                Try Again
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
