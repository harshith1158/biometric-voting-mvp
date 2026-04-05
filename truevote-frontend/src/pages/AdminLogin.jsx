import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AdminLogin() {
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = () => {
    if (password === 'admin123') {
      localStorage.setItem('admin', 'true');
      navigate('/admin');
    } else {
      alert('Invalid password');
    }
  };

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4 py-10">
      <div className="w-full max-w-md rounded-xl bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 p-8 hover:scale-[1.02]">
        <div className="mb-6 text-center">
          <p className="inline-flex rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-orange-300">
            TRUE VOTE Admin
          </p>
          <h2 className="mt-4 text-2xl font-bold text-white">Admin Login</h2>
          <p className="mt-2 text-sm text-gray-300">Secure control access for election supervision.</p>
        </div>

        <input
          type="password"
          placeholder="Enter password"
          className="w-full rounded-xl border border-white/20 bg-white/10 text-white p-3 transition-all duration-300 focus:border-green-500 focus:outline-none focus:ring-2 focus:ring-green-400/40"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleLogin();
            }
          }}
        />

        <button
          onClick={handleLogin}
          className="mt-4 w-full rounded-xl bg-gradient-to-r from-orange-500 to-green-500 px-4 py-3 text-white shadow-lg transition-all duration-300 hover:scale-105"
        >
          Login
        </button>
      </div>
    </div>
  );
}