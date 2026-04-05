import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerVoter } from "../services/api";

export default function OTP() {
  const navigate = useNavigate();
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const aadharNumber = localStorage.getItem("aadhar");
    if (!aadharNumber) {
      navigate("/");
    }
  }, [navigate]);

  const handleVerify = async () => {
    if (otp.length !== 6) {
      setError("OTP must be 6 digits");
      setMessage("");
      return;
    }

    const aadharNumber = localStorage.getItem("aadhar");
    if (!aadharNumber) {
      setError("Aadhaar not found. Please register again.");
      setMessage("");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("Processing registration...");

    try {
      console.log("Calling registerVoter API with Aadhaar:", aadharNumber);
      const res = await registerVoter(aadharNumber);
      
      console.log("Registration response:", res.data);
      
      // Handle both new and existing voter responses
      if (res?.data?.epic_id) {
        localStorage.setItem("epic", res.data.epic_id);
        
        // Store voter_id if provided
        if (res.data.voter_id) {
          localStorage.setItem("voter_id", res.data.voter_id);
        }
        
        setError("");
        // Show message based on status
        if (res.data.status === "existing") {
          setMessage("Welcome back! Using your existing registration...");
        } else {
          setMessage("Registration successful! Proceeding to liveness...");
        }
        
        setTimeout(() => navigate("/liveness"), 1500);
      } else {
        setError("No epic_id in response");
        setMessage("");
      }
    } catch (err) {
      console.error("Registration error:", err);
      const msg = err?.response?.data?.error || err?.message || "Registration failed";
      alert(msg);
      
      // Check if error indicates existing voter
      if (err?.response?.data?.status === "existing" && err?.response?.data?.epic_id) {
        localStorage.setItem("epic", err.response.data.epic_id);
        if (err.response.data.voter_id) {
          localStorage.setItem("voter_id", err.response.data.voter_id);
        }
        setError("");
        setMessage("Aadhaar already registered. Proceeding to liveness...");
        setTimeout(() => navigate("/liveness"), 1500);
      } else {
        setError(msg);
        setMessage("");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-blue-600 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center mb-2">OTP Verification</h1>
        <p className="text-center text-gray-600 mb-6">OTP sent to registered mobile</p>

        <input
          type="text"
          inputMode="numeric"
          maxLength={6}
          className="w-full border rounded-lg px-4 py-3 mb-3 text-center tracking-widest text-lg"
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
          placeholder="Enter 6-digit OTP"
        />

        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

        {message && <p className="text-green-600 text-sm mb-3">{message}</p>}

        <button
          type="button"
          onClick={handleVerify}
          disabled={loading}
          className="w-full bg-blue-600 text-white rounded-lg shadow-md py-3 font-semibold disabled:opacity-60"
        >
          {loading ? "Verifying..." : "Verify"}
        </button>
      </div>
    </div>
  );
}
