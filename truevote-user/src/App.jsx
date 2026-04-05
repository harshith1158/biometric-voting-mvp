import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Register from './pages/Register';
import OTP from './pages/OTP';
import Liveness from './pages/Liveness';
import Success from './pages/Success';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Register />} />
        <Route path="/otp" element={<OTP />} />
        <Route path="/liveness" element={<Liveness />} />
        <Route path="/success" element={<Success />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
