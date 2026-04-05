import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import RegistrationStepBar from '../components/RegistrationStepBar';

export default function Success() {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const epic = localStorage.getItem('tv_epic') || 'N/A';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(epic);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="text-center mt-12 px-4 transition-all duration-300 ease-in-out">
      <div className="max-w-2xl mx-auto">
        <RegistrationStepBar current="complete" />
      </div>

      <div className="bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 p-6 rounded-xl max-w-md mx-auto hover:scale-[1.02]">
        <p className="text-sm text-gray-300 mb-2">Enrollment Completed Successfully</p>
        <div className="text-green-600 text-6xl animate-pulse">✔</div>

        <h2 className="text-xl font-bold text-white mt-3">Registration Successful</h2>

        <div className="bg-white/10 text-gray-100 p-3 rounded mt-2 font-mono text-lg max-w-md mx-auto">{epic}</div>

        <button
          className="mt-3 bg-gradient-to-r from-orange-500 to-green-500 text-white px-4 py-2 rounded transition-all duration-300 ease-in-out"
          onClick={handleCopy}
        >
          {copied ? 'Copied!' : 'Copy EPIC'}
        </button>

        <div>
          <button
            className="mt-3 bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-xl shadow-lg transition-all duration-300 ease-in-out hover:scale-105 w-full font-semibold"
            onClick={() => navigate('/booth-login')}
          >
            Proceed to Booth →
          </button>
        </div>
      </div>

      {copied ? <p className="text-sm text-emerald-300 mt-4">Copied to clipboard</p> : null}
    </div>
  );
}
