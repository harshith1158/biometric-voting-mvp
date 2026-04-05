import React from 'react';

export default function About() {
  return (
    <div className="min-h-screen bg-black text-white p-4 md:p-10 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-extrabold mb-8 bg-gradient-to-r from-orange-400 via-white to-green-400 bg-clip-text text-transparent">
          About TRUE VOTE
        </h1>

        <div className="space-y-6 text-gray-300 leading-relaxed">
          <p className="text-lg">
            TRUE VOTE is a research prototype designed to demonstrate a secure, biometric-based digital voting system
            leveraging cutting-edge identity verification and blockchain technology.
          </p>

          <div className="bg-white/5 border border-white/10 rounded-xl p-6 backdrop-blur-md">
            <h2 className="text-2xl font-bold text-white mb-4">Core Features</h2>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <span className="text-green-400 font-bold">✓</span>
                <span><strong>Aadhaar-Based Identity Simulation:</strong> Mock UIDAI-secure authentication flow with Aadhaar verification</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 font-bold">✓</span>
                <span><strong>Liveness Detection:</strong> AI-powered face liveness detection to prevent spoofing attacks</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 font-bold">✓</span>
                <span><strong>Fingerprint Verification:</strong> Biometric matching against registered fingerprint datasets</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 font-bold">✓</span>
                <span><strong>Blockchain Integrity:</strong> Hash chain system for tamper-proof vote tracking</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-green-400 font-bold">✓</span>
                <span><strong>Duplicate Vote Prevention:</strong> Ensures each Aadhaar-linked EPIC ID votes only once</span>
              </li>
            </ul>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-6 backdrop-blur-md">
            <h2 className="text-2xl font-bold text-white mb-4">Technical Stack</h2>
            <p className="mb-3">
              <strong>Frontend:</strong> React + Vite + TailwindCSS for ultra-responsive UI
            </p>
            <p className="mb-3">
              <strong>Backend:</strong> Flask + SQLAlchemy with MediaPipe liveness detection
            </p>
            <p>
              <strong>Biometrics:</strong> Fingerprint matching, face detection, and identity simulation
            </p>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-6 backdrop-blur-md">
            <h2 className="text-2xl font-bold text-white mb-4">Research Focus</h2>
            <p>
              TRUE VOTE demonstrates how modern biometric technologies can be integrated into democratic voting systems
              to enhance security, accessibility, and voter confidence. The system simulates real-world authentication
              challenges while maintaining privacy and preventing unauthorized access.
            </p>
          </div>

          <p className="text-center text-gray-400 text-sm mt-10 pt-6 border-t border-white/10">
            TRUE VOTE is a proof-of-concept system developed for educational and research purposes.
          </p>
        </div>
      </div>
    </div>
  );
}
