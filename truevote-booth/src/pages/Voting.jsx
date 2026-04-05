import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../services/api';

function moveNotaLast(candidates) {
  const normal = candidates.filter((candidate) => candidate.name !== 'NOTA');
  const nota = candidates.find((candidate) => candidate.name === 'NOTA');

  return nota ? [...normal, nota] : normal;
}

function Voting() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;

    async function loadCandidates() {
      try {
        const response = await API.get('/candidates');
        if (!active) {
          return;
        }

        setCandidates(moveNotaLast(response.data?.candidates ?? []));
      } catch (requestError) {
        if (!active) {
          return;
        }

        setError(requestError.response?.data?.error ?? 'Unable to fetch candidates.');
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadCandidates();

    return () => {
      active = false;
    };
  }, []);

  const handleSubmitVote = async () => {
    const epicId = localStorage.getItem('epic');
    if (!selectedId || !epicId) {
      setError('Select a candidate and ensure the EPIC ID is present.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const response = await API.post('/cast_vote', {
        epic_id: epicId,
        candidate_id: selectedId,
      });

      localStorage.setItem('voteResult', JSON.stringify(response.data));
      navigate('/result');
    } catch (requestError) {
      const voteError = requestError.response?.data?.error ?? 'Vote failed';
      setError(voteError);
      alert(voteError);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen px-4 py-8 md:px-8 md:py-12">
      <section className="mx-auto max-w-6xl">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="mb-3 inline-flex rounded-full bg-sky-100 px-3 py-1 text-sm font-medium text-sky-800">
              Ballot Selection
            </p>
            <h1 className="font-display text-4xl font-semibold text-slate-900">Choose one candidate</h1>
            <p className="mt-3 max-w-2xl text-base text-slate-600">
              Tap a large ballot card to select a candidate. NOTA remains at the end of the list.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-600">
            EPIC: <span className="font-semibold text-slate-900">{localStorage.getItem('epic')}</span>
          </div>
        </div>

        {loading ? (
          <div className="panel p-10 text-center text-slate-600">Loading candidates...</div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {candidates.map((candidate) => {
              const isSelected = selectedId === candidate.id;

              return (
                <button
                  key={candidate.id}
                  className={`panel min-h-56 cursor-pointer p-6 text-left transition ${
                    isSelected
                      ? 'border-green-500 bg-green-50 ring-4 ring-green-100'
                      : 'hover:-translate-y-1 hover:border-green-300 hover:bg-white'
                  }`}
                  type="button"
                  onClick={() => setSelectedId(candidate.id)}
                >
                  <div className="flex h-full flex-col justify-between gap-6">
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Candidate</p>
                      <h2 className="mt-3 font-display text-3xl font-semibold text-slate-900">{candidate.name}</h2>
                    </div>
                    <div className="space-y-2 text-base text-slate-600">
                      <p>
                        <span className="font-semibold text-slate-900">Party:</span> {candidate.party}
                      </p>
                      <p>
                        <span className="font-semibold text-slate-900">State:</span> {candidate.state}
                      </p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {error ? <p className="mt-6 text-sm font-medium text-rose-600">{error}</p> : null}

        <div className="mt-8 flex flex-col gap-4 sm:flex-row">
          <button
            className="primary-button min-w-52"
            type="button"
            onClick={handleSubmitVote}
            disabled={loading || submitting || !selectedId}
          >
            {submitting ? 'Submitting Vote...' : 'Submit Vote'}
          </button>
          <button
            className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-6 py-3 text-base font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
            type="button"
            onClick={() => navigate('/')}
          >
            Restart Flow
          </button>
        </div>
      </section>
    </main>
  );
}

export default Voting;