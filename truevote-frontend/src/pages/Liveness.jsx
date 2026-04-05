import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FaceDetection } from '@mediapipe/face_detection';
import { checkLiveness } from '../services/api';
import RegistrationStepBar from '../components/RegistrationStepBar';

export default function Liveness() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const detectorRef = useRef(null);
  const rafRef = useRef(null);
  const [streaming, setStreaming] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [frames, setFrames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const voterId = localStorage.getItem('tv_voter_id');

  useEffect(() => {
    startWebcam();
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      if (detectorRef.current) {
        detectorRef.current.close();
      }
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
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (results?.detections?.length > 0) {
        const box = results.detections[0].boundingBox;

        ctx.strokeStyle = 'lime';
        ctx.lineWidth = 3;

        ctx.strokeRect(
          box.xCenter * canvas.width - (box.width * canvas.width) / 2,
          box.yCenter * canvas.height - (box.height * canvas.height) / 2,
          box.width * canvas.width,
          box.height * canvas.height
        );
      }
    });

    detectorRef.current = faceDetection;
  }, []);

  const startWebcam = async () => {
    try {
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
            if (
              detectorRef.current &&
              videoRef.current &&
              videoRef.current.readyState >= 2
            ) {
              await detectorRef.current.send({ image: videoRef.current });
            }
            rafRef.current = requestAnimationFrame(detectFrame);
          };

          detectFrame();
        };

        setStreaming(true);
      }
    } catch (err) {
      setError('Failed to access webcam. Please enable camera permissions.');
    }
  };

  const stopWebcam = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((track) => track.stop());
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
    if (!voterId) {
      setError('Voter ID missing. Complete OTP registration first.');
      return;
    }

    setCapturing(true);
    setFrames([]);
    setMessage('Capturing frames... Please blink naturally');
    setError('');

    const capturedFrames = [];
    const frameCount = 5;
    const intervalMs = 500;

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
      const formData = new FormData();
      capturedFrames.forEach((frame, index) => {
        formData.append('frames', frame, `frame_${index}.jpg`);
      });
      formData.append('voter_id', voterId);

      const response = await checkLiveness(formData);

      if (response.data.liveness === 'pass') {
        setResult({
          status: 'pass',
          message: 'Liveness check passed!',
          earValues: response.data.ear_values,
          biometricId: response.data.biometric_id,
        });
        if (response.data.biometric_id) {
          localStorage.setItem('tv_biometric_id', String(response.data.biometric_id));
        }
        setMessage('Verification successful. Redirecting...');
        setTimeout(() => navigate('/success'), 1500);
      } else {
        setResult({
          status: 'fail',
          message: 'Liveness check failed. Please try again.',
          earValues: response.data.ear_values || [],
        });
        setMessage('');
      }
    } catch (err) {
      const livenessError = err.response?.data?.error || 'Liveness failed';
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
        className="bg-white/5 border border-white/10 backdrop-blur-md rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition duration-300 p-8 max-w-2xl w-full mx-auto"
      >
        <RegistrationStepBar current="liveness" />

        <p className="text-sm text-gray-300 text-center mb-1">Biometric Verification in Progress</p>
        <h2 className="text-3xl font-bold text-center text-white mb-4">
          Liveness Detection
        </h2>
        <p className="text-center text-gray-300 mb-8">
          Align your face and move slightly
        </p>

        <div className="flex flex-col items-center mt-6">
          <div className="relative bg-black rounded-xl shadow-lg border overflow-hidden">
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

          <p className="mt-3 text-gray-300">Align your face and move slightly</p>

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
              Frames captured: {frames.length}/5
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
                setMessage('');
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:scale-105 mt-4 w-full"
            >
              Try Again
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
