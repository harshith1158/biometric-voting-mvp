import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { castVote, getCandidates, captureFingerprint } from '../services/api';
import CandidateCard from '../components/CandidateCard';

const CANDIDATE_IMAGES = {
  'narendra modi':  { image: '/images/Narendra Modi.jpg',   logo: '/images/BJP.jpg'  },
  'rahul gandhi':   { image: '/images/Rahul Gandhi.jpg',    logo: '/images/INC.png'  },
  'revanth reddy':  { image: '/images/Revanth Reddy.png',   logo: '/images/TDP.png'  },
  'stalin':         { image: '/images/Stalin.jpg',          logo: '/images/DMK.png'  },
  'joseph vijay':   { image: '/images/Joeseph Vijay.jpg',   logo: '/images/TVK.jpg'  },
  'nota':           { image: '/images/NOTA.png',            logo: '/images/NOTA.png' },
};

function injectImages(candidate) {
  const key = String(candidate.name || '').toLowerCase();
  const assets = CANDIDATE_IMAGES[key] || {};
  return { ...candidate, ...assets };
}

function normalizeCandidates(raw) {
  const candidates = Array.isArray(raw) ? raw : [];
  const regular = candidates.filter((c) => String(c.name || '').toUpperCase() !== 'NOTA');
  const nota = candidates.find((c) => String(c.name || '').toUpperCase() === 'NOTA');

  if (nota) {
    return [...regular.map(injectImages), injectImages(nota)];
  }

  return [
    ...regular.map(injectImages),
    injectImages({
      id: 'nota',
      name: 'NOTA',
      party: 'None of the Above',
      state: 'All Constituencies',
    }),
  ];
}

export default function BoothVoting() {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [voteSuccess, setVoteSuccess] = useState(false);
  const [error, setError] = useState('');
  const [fpVerifying, setFpVerifying] = useState(false);
  const [fpError, setFpError] = useState('');

  const epic = localStorage.getItem('tv_epic') || '';

  useEffect(() => {
    const fetchCandidates = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await getCandidates();
        setCandidates(normalizeCandidates(response?.data?.candidates));
      } catch (err) {
        setError(err?.response?.data?.error || 'Failed to load candidates.');
      } finally {
        setLoading(false);
      }
    };

    fetchCandidates();
  }, []);

  const selectedCandidate = useMemo(
    () => candidates.find((candidate) => String(candidate.id) === String(selectedCandidateId)),
    [candidates, selectedCandidateId]
  );

  const createRipple = (event) => {
    const button = event.currentTarget;

    const circle = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${event.clientX - button.offsetLeft - radius}px`;
    circle.style.top = `${event.clientY - button.offsetTop - radius}px`;
    circle.classList.add('ripple');

    const ripple = button.getElementsByClassName('ripple')[0];
    if (ripple) {
      ripple.remove();
    }

    button.appendChild(circle);
  };

  const handleFingerprintVote = async () => {
    if (!epic) {
      setFpError('EPIC ID missing. Please login again.');
      return;
    }

    setFpVerifying(true);
    setFpError('');

    try {
      await captureFingerprint({ epic_id: epic });

      setSubmitting(true);
      const response = await castVote({
        epic_id: epic,
        candidate_id: selectedCandidateId,
      });

      localStorage.setItem('tv_vote_result', JSON.stringify(response?.data || {}));
      localStorage.setItem('tv_voted_candidate', JSON.stringify({
        name: selectedCandidate?.name || '',
        party: selectedCandidate?.party || '',
      }));

      setShowModal(false);
      setVoteSuccess(true);

      setTimeout(() => {
        navigate('/vote-confirm');
      }, 2000);
    } catch (err) {
      setFpError(err?.response?.data?.error || 'Fingerprint scan failed or vote could not be cast.');
    } finally {
      setFpVerifying(false);
      setSubmitting(false);
    }
  };

  const handleCandidateClick = (id) => {
    setSelectedCandidateId(id);
    setFpError('');
    setShowModal(true);
  };

  const regularCandidates = candidates.filter(
    (c) => String(c.name || '').toUpperCase() !== 'NOTA'
  );
  const notaCandidate = candidates.find(
    (c) => String(c.name || '').toUpperCase() === 'NOTA'
  );

  if (localStorage.getItem('tv_result_declared') === 'true') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center text-center px-4">
        <div className="bg-red-900/20 border border-red-500/40 rounded-2xl p-10 max-w-sm">
          <p className="text-5xl mb-4">🔒</p>
          <h2 className="text-2xl font-bold text-red-300 mb-2">Voting Closed</h2>
          <p className="text-gray-400 text-sm mb-6">The election result has been declared.</p>
          <button
            onClick={() => navigate('/result')}
            className="bg-gradient-to-r from-orange-500 to-green-500 text-white px-6 py-2 rounded-xl hover:scale-105 transition-all duration-300 font-semibold"
          >
            View Result
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      {voteSuccess && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 p-8 rounded-xl text-center animate-bounce">
            <h2 className="text-2xl font-bold text-green-300">Vote Cast Successfully</h2>
            <p className="text-gray-300 mt-2">Thank you for voting</p>
          </div>
        </div>
      )}

      <div className="px-4 py-10 pb-10 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="max-w-6xl mx-auto">
        <p className="text-center text-sm text-gray-300 mb-1">Cast Your Vote Securely</p>
        <h2 className="text-3xl md:text-4xl font-bold text-white text-center">Cast Your Vote</h2>
        <div className="text-center text-sm text-gray-300 mb-3 mt-2">
          🔐 Your vote is anonymous and securely recorded
        </div>

        {error ? (
          <div className="mt-6 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 px-4 py-3">{error}</div>
        ) : null}

        {loading ? (
          <div className="flex justify-center mt-8">
            <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mt-8">
            {regularCandidates.map((candidate) => {
              const selected = String(selectedCandidateId) === String(candidate.id);
              return (
                <div
                  key={candidate.id}
                  onClick={() => handleCandidateClick(candidate.id)}
                  className="transition-all duration-300 ease-in-out cursor-pointer"
                >
                  <CandidateCard
                    candidate={candidate}
                    isSelected={selected}
                    onSelect={() => handleCandidateClick(candidate.id)}
                  />
                </div>
              );
            })}

            {notaCandidate && (
              <div
                onClick={() => handleCandidateClick(notaCandidate.id)}
                className={`cursor-pointer rounded-xl border-2 transition-all duration-300 flex flex-col justify-center items-center bg-white/5 backdrop-blur-md shadow-lg hover:shadow-xl overflow-hidden ${
                  String(selectedCandidateId) === String(notaCandidate.id)
                    ? 'bg-yellow-500/20 border-yellow-400 shadow-lg scale-105'
                    : 'bg-yellow-500/10 border-yellow-500/40 hover:shadow-md hover:scale-105'
                }`}
              >
                <div className="w-full h-40 overflow-hidden">
                  <img
                    src="/images/NOTA.png"
                    alt="NOTA"
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="p-4 text-center">
                  <h2 className="text-xl font-bold text-yellow-200">NOTA</h2>
                  <p className="text-sm text-yellow-100 mt-1">None of the Above</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Click a candidate card to cast your vote */}

        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 px-4">
            <div className="bg-gray-900 p-6 rounded-xl w-full max-w-sm text-center border border-gray-700">
              <h2 className="text-xl text-white mb-1 font-bold">Confirm Vote with Fingerprint</h2>
              <p className="text-sm text-gray-400 mb-4">
                Voting for: <span className="text-white font-semibold">{selectedCandidate?.name}</span>
              </p>

              <div className="mb-4 flex flex-col items-center gap-3">
                <div className={`flex h-20 w-20 items-center justify-center rounded-full border-4 ${
                  fpVerifying ? 'border-green-400 animate-pulse' : 'border-gray-600'
                } bg-gray-800`}>
                  <span className="text-3xl">◎</span>
                </div>
                <p className="text-sm text-gray-300">
                  {fpVerifying ? 'Scanning fingerprint...' : 'Place your finger on the FM220U scanner'}
                </p>
              </div>

              {fpError && (
                <p className="text-red-400 text-sm mb-3 text-left">{fpError}</p>
              )}

              <button
                className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-white w-full mb-2 font-semibold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleFingerprintVote}
                disabled={fpVerifying || submitting}
              >
                {fpVerifying ? 'Scanning...' : submitting ? 'Casting Vote...' : 'Scan Fingerprint & Vote'}
              </button>

              <button
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-white w-full transition-all duration-300 disabled:opacity-50"
                onClick={() => { setShowModal(false); setFpError(''); }}
                disabled={fpVerifying || submitting}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
      </div>
    </>
  );
}
