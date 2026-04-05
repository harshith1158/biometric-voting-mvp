import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitLivenessFrames } from "../services/api";

export default function Liveness() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [cameraStarted, setCameraStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    const epic = localStorage.getItem("epic");
    if (!epic) {
      navigate("/otp");
      return undefined;
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [navigate, stream]);

  const startCamera = async () => {
    setError("");
    try {
      const media = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user"
        }, 
        audio: false 
      });
      setStream(media);
      if (videoRef.current) {
        videoRef.current.srcObject = media;
        // Wait for video to load
        videoRef.current.onloadedmetadata = () => {
          console.log(`[Camera] Video stream loaded: ${videoRef.current.videoWidth}x${videoRef.current.videoHeight}`);
          videoRef.current.play();
        };
      }
      setCameraStarted(true);
      setStatus("✓ Camera started - Position your face in the center");
    } catch (err) {
      console.error("[Camera] Error:", err);
      let msg = "Unable to access camera";
      if (err.name === "NotAllowedError") {
        msg = "Permission denied. Please allow camera access in browser settings.";
      } else if (err.name === "NotFoundError") {
        msg = "No camera found. Please check your device.";
      } else if (err.name === "NotReadableError") {
        msg = "Camera is in use by another application.";
      }
      setError(msg);
    }
  };

  const captureSingleFrame = () => {
    if (!videoRef.current || !canvasRef.current) {
      return Promise.resolve(null);
    }

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext("2d");
    
    // Ensure video is ready
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      console.warn("Video not ready, dimensions are 0");
      return Promise.resolve(null);
    }
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return new Promise((resolve) => {
      // Use HIGH quality JPEG (0.95 = 95% quality, not default ~0.75)
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.95);
    });
  };

  const verifyLiveness = async () => {
    if (!cameraStarted) {
      setError("Start camera before liveness verification.");
      return;
    }

    setLoading(true);
    setError("");
    setStatus("Blink your eyes");

    try {
      const video = videoRef.current;
      
      // Wait for video stream to be ready
      if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
        throw new Error("Video stream not ready. Please ensure camera is fully loaded.");
      }
      
      console.log(`[Liveness] Video ready: ${video.videoWidth}x${video.videoHeight}`);
      
      const captured = [];
      for (let i = 0; i < 5; i += 1) {
        console.log(`[Liveness] Capturing frame ${i + 1}/5...`);
        const frame = await captureSingleFrame();
        
        if (frame) {
          console.log(`[Liveness] Frame ${i + 1} captured: ${frame.size} bytes`);
          captured.push(frame);
        } else {
          console.warn(`[Liveness] Frame ${i + 1} was null`);
        }
        
        if (i < 4) {
          // Wait 500ms between frames
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      }

      if (captured.length !== 5) {
        throw new Error(`Only captured ${captured.length}/5 frames. Please try again.`);
      }

      console.log(`[Liveness] All 5 frames captured successfully`);

      const voterId = localStorage.getItem("voter_id");
      const epic = localStorage.getItem("epic");
      
      console.log(`[Liveness] Submission - voter_id: ${voterId}, epic: ${epic}`);
      
      if (!voterId) {
        throw new Error("voter_id not found in localStorage. Please register again.");
      }

      const formData = new FormData();
      formData.append("voter_id", voterId);
      
      // Add all captured frames
      captured.forEach((frame, index) => {
        formData.append("frames", frame, `frame-${index + 1}.jpg`);
      });

      console.log(`[Liveness] Submitting to backend with ${captured.length} frames...`);
      const res = await submitLivenessFrames(formData);
      
      console.log(`[Liveness] Response status: ${res.status}`, res.data);
      
      if (res?.data?.liveness === "pass") {
        setStatus("✓ Liveness verified!");
        setTimeout(() => navigate("/success"), 1000);
        return;
      }

      setError(res?.data?.message || "Liveness check did not pass. Please try again.");
    } catch (err) {
      console.error("[Liveness] Error object:", err);
      console.error("[Liveness] Response:", err?.response);
      console.error("[Liveness] Response data:", err?.response?.data);
      
      let msg = "Liveness request failed";
      
      if (err?.response?.data?.error) {
        msg = err.response.data.error;
      } else if (err?.response?.data?.message) {
        msg = err.response.data.message;
      } else if (err?.response?.status === 400) {
        msg = `Error: ${err.response.data.error || JSON.stringify(err.response.data)}`;
      } else if (err?.message) {
        msg = err.message;
      }
      
      setError(msg);
      alert(err?.response?.data?.error || "Liveness failed");
      console.log("[Liveness] Final error message:", msg);
    } finally {
      setLoading(false);
      setStatus("");
    }
  };

  return (
    <div className="min-h-screen bg-blue-600 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center mb-2">Liveness Check</h1>
        <p className="text-center text-gray-600 mb-4">Blink your eyes</p>

        <div className="w-full overflow-hidden rounded-lg bg-black mb-4">
          <video ref={videoRef} autoPlay playsInline className="w-full h-64 object-cover" />
        </div>
        <canvas ref={canvasRef} className="hidden" />

        {status && <p className="text-sm text-gray-700 mb-3 text-center">{status}</p>}
        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

        <div className="space-y-3">
          <button
            type="button"
            onClick={startCamera}
            className="w-full bg-blue-600 text-white rounded-lg shadow-md py-3 font-semibold"
          >
            Start Camera
          </button>
          <button
            type="button"
            onClick={verifyLiveness}
            disabled={loading}
            className="w-full bg-blue-600 text-white rounded-lg shadow-md py-3 font-semibold disabled:opacity-60"
          >
            {loading ? "Verifying..." : "Verify Liveness"}
          </button>
        </div>
      </div>
    </div>
  );
}
