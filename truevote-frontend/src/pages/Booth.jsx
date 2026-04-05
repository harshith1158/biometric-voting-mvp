import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getCandidates, castVote } from '../services/api';
import CandidateCard from '../components/CandidateCard';

export default function Booth({ epicId, voterId }) {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    try {
      const response = await getCandidates();
      setCandidates(response.data.candidates);
    } catch (err) {
      setError('Failed to load candidates');
    }
  };

  const handleCastVote = async () => {
    if (!selectedCandidate) {
      setError('Please select a candidate');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('Casting your vote...');

    try {
      const response = await castVote({
        epic_id: epicId,
        candidate_id: selectedCandidate.id,
      });

      setMessage('Vote cast successfully!');
      setTimeout(() => navigate('/result'), 2000);
    } catch (err) {
      const voteError = err.response?.data?.error || 'Vote failed';
      setError(voteError);
      alert(voteError);
      setMessage('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 py-12 px-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="max-w-6xl mx-auto"
      >
        <h2 className="text-4xl font-bold text-center text-gray-800 mb-12">
          Select Your Candidate
        </h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {message && (
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-6">
            {message}
          </div>
        )}

        <motion.div
          layout
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8"
        >
          {candidates.map((candidate, index) => (
            <motion.div
              key={candidate.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <CandidateCard
                candidate={candidate}
                isSelected={selectedCandidate?.id === candidate.id}
                onSelect={() => setSelectedCandidate(candidate)}
              />
            </motion.div>
          ))}
        </motion.div>

        {selectedCandidate && !confirmed && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-lg p-6 mb-6"
          >
            <h3 className="text-lg font-bold text-gray-800 mb-4">
              Confirm Your Vote
            </h3>
            <div className="bg-blue-50 p-4 rounded mb-4">
              <p className="text-gray-700">
                You are about to vote for:{' '}
                <span className="font-bold text-blue-600">
                  {selectedCandidate.name}
                </span>
                <br />
                Party: <span className="font-bold">{selectedCandidate.party}</span>
              </p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => {
                  setConfirmed(true);
                }}
                className="btn-primary flex-1"
              >
                Confirm Vote
              </button>
              <button
                onClick={() => setSelectedCandidate(null)}
                className="btn-secondary flex-1"
              >
                Change Selection
              </button>
            </div>
          </motion.div>
        )}

        {confirmed && selectedCandidate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <h3 className="text-lg font-bold text-gray-800 mb-4">
              Final Confirmation
            </h3>
            <div className="bg-yellow-50 border border-yellow-400 p-4 rounded mb-4">
              <p className="text-yellow-800 font-semibold">
                ⚠ Your vote is about to be recorded on the blockchain. This action cannot be undone.
              </p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={handleCastVote}
                disabled={loading}
                className="btn-primary flex-1"
              >
                {loading ? 'Casting Vote...' : 'Cast Vote'}
              </button>
              <button
                onClick={() => {
                  setConfirmed(false);
                  setSelectedCandidate(null);
                }}
                disabled={loading}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
