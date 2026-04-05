import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { motion } from 'framer-motion';
import confetti from 'canvas-confetti';
import { playSuccessSound } from '../utils/soundHelpers';

const PARTY_LOGOS = {
  'narendra modi':  { logo: '/images/BJP.jpg',  party: 'BJP' },
  'rahul gandhi':   { logo: '/images/INC.png',  party: 'INC' },
  'revanth reddy':  { logo: '/images/TDP.png',  party: 'TDP' },
  'stalin':         { logo: '/images/DMK.png',  party: 'DMK' },
  'joseph vijay':   { logo: '/images/TVK.jpg',  party: 'TVK' },
  'nota':           { logo: '/images/NOTA.png', party: 'NOTA' },
};

export default function VoteConfirm() {
  const navigate = useNavigate();

  const raw = localStorage.getItem('tv_voted_candidate');
  const voted = raw ? JSON.parse(raw) : null;

  const key = String(voted?.name || '').toLowerCase();
  const assets = PARTY_LOGOS[key] || {};
  const partyName = voted?.party || assets.party || voted?.name || 'your chosen party';
  const partyLogo = assets.logo || null;

  useEffect(() => {
    playSuccessSound();
    setTimeout(() => {
      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 }, colors: ['#ff9933', '#ffffff', '#16a34a'] });
    }, 200);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 130 }}
        className="bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-10 max-w-sm w-full text-center shadow-[0_0_40px_rgba(34,197,94,0.2)]"
      >
        {/* Checkmark */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.15, type: 'spring', stiffness: 200 }}
          className="w-20 h-20 mx-auto rounded-full bg-green-500/20 border-2 border-green-400 flex items-center justify-center text-4xl mb-6"
        >
          ✓
        </motion.div>

        <p className="text-gray-400 text-sm uppercase tracking-widest mb-2">Vote Recorded</p>
        <h1 className="text-2xl font-extrabold text-white mb-6">You have voted for</h1>

        {/* Party logo + name */}
        <div className="flex flex-col items-center gap-3 mb-8">
          {partyLogo && (
            <img
              src={partyLogo}
              alt={partyName}
              className="w-24 h-24 rounded-2xl object-contain bg-white/10 p-2 border border-white/20 shadow-lg"
            />
          )}
          <span className="text-3xl font-bold bg-gradient-to-r from-orange-400 via-white to-green-400 bg-clip-text text-transparent">
            {partyName}
          </span>
        </div>

        <p className="text-gray-400 text-xs mb-8">
          Your vote has been securely recorded on the ledger.
        </p>

        <button
          onClick={() => {
            localStorage.removeItem('tv_vote_result');
            localStorage.removeItem('tv_epic');
            localStorage.removeItem('tv_voted_candidate');
            navigate('/');
          }}
          className="bg-gradient-to-r from-orange-500 to-green-500 text-white px-10 py-3 rounded-xl shadow-lg transition-all duration-300 hover:scale-105 font-semibold w-full"
        >
          Home
        </button>
      </motion.div>
    </div>
  );
}
