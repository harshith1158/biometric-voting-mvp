import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import confetti from 'canvas-confetti';
import { playSuccessSound } from '../utils/soundHelpers';
import { getCandidates } from '../services/api';

// Keyed by lowercase candidate name → party logo path
const PARTY_LOGOS = {
  'narendra modi':  '/images/BJP.jpg',
  'rahul gandhi':   '/images/INC.png',
  'revanth reddy':  '/images/TDP.png',
  'stalin':         '/images/DMK.png',
  'joseph vijay':   '/images/TVK.jpg',
  'nota':           '/images/NOTA.png',
};

const getPartyLogo = (name) => PARTY_LOGOS[String(name || '').toLowerCase()] || null;
const getVotes = (c) => Number(c?.votes ?? c?.vote_count ?? c?.voteCount ?? 0) || 0;

export default function Result() {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [winner, setWinner] = useState(null);
  const [loadingCandidates, setLoadingCandidates] = useState(true);

  const voteResultRaw = localStorage.getItem('tv_vote_result');
  const hasVerifiedVote = Boolean(voteResultRaw);

  useEffect(() => {
    getCandidates()
      .then((res) => {
        const list = Array.isArray(res?.data?.candidates)
          ? res.data.candidates
          : Array.isArray(res?.data) ? res.data : [];
        setCandidates(list);

        const total = list.reduce((sum, c) => sum + getVotes(c), 0);

        if (total > 0) {
          // Only declare a winner when votes actually exist
          const top = list.reduce((prev, curr) => getVotes(curr) > getVotes(prev) ? curr : prev);
          setWinner(top);

          playSuccessSound();
          setTimeout(() => {
            confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 }, colors: ['#ff9933', '#ffffff', '#16a34a'] });
            setTimeout(() => {
              confetti({ particleCount: 60, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#ff9933', '#ffffff', '#16a34a'] });
              confetti({ particleCount: 60, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#ff9933', '#ffffff', '#16a34a'] });
            }, 600);
          }, 300);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingCandidates(false));
  }, []);

  const handleReturnHome = () => {
    localStorage.removeItem('tv_vote_result');
    navigate('/');
  };

  const totalVotes = candidates.reduce((sum, c) => sum + getVotes(c), 0);
  const winnerVotes = winner ? getVotes(winner) : 0;

  return (
    <div className="min-h-screen px-4 py-10 transition-opacity duration-500 opacity-100">
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <p className="text-sm text-gray-400 uppercase tracking-widest mb-2">Official Election Result</p>
          <h1 className="text-4xl font-extrabold text-white">
            <span className="bg-gradient-to-r from-orange-400 via-white to-green-400 bg-clip-text text-transparent">
              Election Result
            </span>
          </h1>
        </motion.div>

        {loadingCandidates && (
          <div className="flex justify-center mb-6">
            <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* No votes yet */}
        {!loadingCandidates && totalVotes === 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-10 text-center mb-6"
          >
            <p className="text-5xl mb-4">📊</p>
            <h2 className="text-xl font-bold text-gray-200 mb-2">No Results Yet</h2>
            <p className="text-gray-400 text-sm">Voting is still in progress. No votes have been cast yet.</p>
          </motion.div>
        )}

        {/* Winner Card — only shown when votes > 0 */}
        {!loadingCandidates && winner && totalVotes > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 120 }}
            className="bg-gradient-to-br from-green-900/40 to-green-600/20 border border-green-400/40 rounded-2xl p-8 text-center shadow-[0_0_40px_rgba(34,197,94,0.3)] mb-6"
          >
            <p className="text-green-300 text-xs uppercase tracking-widest font-semibold mb-4">🏆 Winning Party</p>

            {getPartyLogo(winner.name) ? (
              <img
                src={getPartyLogo(winner.name)}
                alt={winner.party}
                className="w-28 h-28 mx-auto rounded-2xl object-contain bg-white/10 p-2 border border-white/20 shadow-lg mb-4"
              />
            ) : (
              <div className="w-28 h-28 mx-auto rounded-2xl bg-green-500/20 flex items-center justify-center text-5xl mb-4">
                🏆
              </div>
            )}

            <h2 className="text-3xl font-extrabold text-white mb-1">{winner.party || winner.name}</h2>
            <div className="inline-flex items-center gap-2 bg-green-500/20 border border-green-400/30 rounded-full px-4 py-1 text-green-200 text-sm mt-2">
              <span className="font-bold text-white">{winnerVotes}</span> votes
              <span className="text-green-400">
                ({Math.round((winnerVotes / totalVotes) * 100)}%)
              </span>
            </div>
          </motion.div>
        )}

        {/* Vote Tally — only shown when votes > 0 */}
        {!loadingCandidates && candidates.length > 0 && totalVotes > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white/5 border border-white/10 backdrop-blur-md rounded-2xl p-5 mb-6"
          >
            <h3 className="text-white font-semibold mb-4 text-sm uppercase tracking-wide">Vote Tally</h3>
            {candidates.map((c) => {
              const votes = getVotes(c);
              const pct = (votes / totalVotes) * 100;
              const isWinner = winner && String(c.id) === String(winner.id);
              const logo = getPartyLogo(c.name);
              return (
                <div key={c.id} className="mb-4 flex items-center gap-3">
                  {logo ? (
                    <img src={logo} alt={c.party} className="w-9 h-9 rounded-lg object-contain bg-white/10 p-1 border border-white/10 flex-shrink-0" />
                  ) : (
                    <div className="w-9 h-9 rounded-lg bg-white/10 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between text-sm mb-1">
                      <span className={`font-semibold truncate ${isWinner ? 'text-green-300' : 'text-gray-200'}`}>
                        {isWinner ? '🏆 ' : ''}{c.party || c.name}
                      </span>
                      <span className="text-gray-300 ml-2 flex-shrink-0">{votes} votes</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-700 ${
                          isWinner
                            ? 'bg-gradient-to-r from-green-400 to-emerald-300 shadow-[0_0_8px_rgba(34,197,94,0.6)]'
                            : 'bg-gradient-to-r from-orange-400/60 to-blue-400/60'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </motion.div>
        )}

        {/* Personal vote confirmation */}
        {hasVerifiedVote && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="bg-green-900/20 border border-green-500/30 rounded-xl px-4 py-3 text-center text-green-300 text-sm mb-6"
          >
            Your vote has been recorded on the secure ledger.
          </motion.div>
        )}

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="flex flex-col items-center gap-3"
        >
          <button
            onClick={handleReturnHome}
            className="bg-gradient-to-r from-orange-500 to-green-500 text-white px-10 py-3 rounded-xl shadow-lg transition-all duration-300 hover:scale-105 font-semibold w-full max-w-xs"
          >
            Return to Home
          </button>
          {localStorage.getItem('tv_result_declared') === 'true' && (
            <button
              onClick={() => {
                localStorage.removeItem('tv_result_declared');
                localStorage.removeItem('tv_vote_result');
                localStorage.removeItem('tv_epic');
                navigate('/');
              }}
              className="bg-white/10 border border-white/20 text-gray-200 px-10 py-3 rounded-xl shadow-lg transition-all duration-300 hover:scale-105 hover:bg-white/20 font-semibold w-full max-w-xs"
            >
              🔄 Restart Election
            </button>
          )}
        </motion.div>

      </div>
    </div>
  );
}
