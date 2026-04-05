import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const navigate = useNavigate();
  const [aadhar, setAadhar] = useState("");
  const [error, setError] = useState("");

  const handleContinue = () => {
    if (aadhar.length !== 12) {
      setError("Enter a valid 12-digit Aadhaar number");
      return;
    }

    localStorage.setItem("aadhar", aadhar);
    setError("");
    navigate("/otp");
  };

  return (
    <div className="min-h-screen bg-blue-600 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center mb-2">TRUE VOTE</h1>
        <p className="text-center text-gray-600 mb-6">User Registration</p>

        <label className="block text-sm font-medium mb-2">Aadhaar Number</label>
        <input
          type="text"
          inputMode="numeric"
          maxLength={12}
          className="w-full border rounded-lg px-4 py-3 mb-3"
          value={aadhar}
          onChange={(e) => setAadhar(e.target.value.replace(/\D/g, "").slice(0, 12))}
          placeholder="Enter 12-digit Aadhaar"
        />

        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

        <button
          type="button"
          className="w-full bg-blue-600 text-white rounded-lg shadow-md py-3 font-semibold"
          onClick={handleContinue}
        >
          Continue
        </button>
      </div>
    </div>
  );
}
