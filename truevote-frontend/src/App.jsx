import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import About from './pages/About';
import FAQ from './pages/FAQ';
import Register from './pages/Register';
import OTP from './pages/OTP';
import Liveness from './pages/Liveness';
import Success from './pages/Success';
import BoothLogin from './pages/BoothLogin';
import VerifyVoter from './pages/VerifyVoter';
import BoothVoting from './pages/BoothVoting';
import Result from './pages/Result';
import VoteConfirm from './pages/VoteConfirm';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import './index.css';

function WatermarkBackground() {
  const location = useLocation();
  const isAdmin = location.pathname === '/admin';
  return (
    <div
      className="absolute inset-0 bg-center bg-contain bg-no-repeat pointer-events-none"
      style={{
        backgroundImage: "url('/images/fingerprint-shield.svg')",
        opacity: isAdmin ? 0.04 : 0.5,
        filter: isAdmin ? 'invert(1) brightness(2) saturate(0.4) hue-rotate(200deg)' : 'none',
      }}
    />
  );
}

function ProtectedAdminRoute() {
  const [isAdmin, setIsAdmin] = useState(localStorage.getItem('admin') === 'true');

  useEffect(() => {
    // Check localStorage on mount to ensure we have the latest value
    setIsAdmin(localStorage.getItem('admin') === 'true');
  }, []);

  useEffect(() => {
    const handleStorageChange = () => {
      setIsAdmin(localStorage.getItem('admin') === 'true');
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  if (!isAdmin) {
    return <Navigate to="/admin-login" replace />;
  }

  return <AdminDashboard />;
}

function App() {
  useEffect(() => {
    // Clear stale vote/fingerprint flags so old browser state cannot fake success.
    ['tv_vote_result', 'tv_verified'].forEach((key) => localStorage.removeItem(key));
  }, []);

  return (
    <div className="min-h-screen bg-[#111827] text-white relative overflow-x-hidden font-sans">
      <BrowserRouter>
        <div className="min-h-screen flex flex-col relative z-10">
          <WatermarkBackground />
          <Navbar />
          <main className="flex-1 transition-all duration-300 ease-in-out">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/about" element={<About />} />
              <Route path="/faq" element={<FAQ />} />
              <Route path="/register" element={<Register />} />
              <Route path="/otp" element={<OTP />} />
              <Route path="/liveness" element={<Liveness />} />
              <Route path="/success" element={<Success />} />
              <Route path="/booth-login" element={<BoothLogin />} />
              <Route path="/verify" element={<VerifyVoter />} />
              <Route path="/booth-voting" element={<BoothVoting />} />
              <Route path="/vote-confirm" element={<VoteConfirm />} />
              <Route path="/result" element={<Result />} />
              <Route path="/admin-login" element={<AdminLogin />} />
              <Route path="/admin" element={<ProtectedAdminRoute />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </BrowserRouter>
    </div>
  );
}

export default App;
