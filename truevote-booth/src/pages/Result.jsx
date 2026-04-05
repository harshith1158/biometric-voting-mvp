import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../services/api';

function Result() {
  const [chainStatus, setChainStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const storedVote = localStorage.getItem('voteResult');
  const hasVerifiedVote = Boolean(storedVote);

  useEffect(() => {
    let active = true;

    async function loadStatus() {
      try {
        const response = await API.get('/chain_status');
        if (!active) {
          return;
        }

        setChainStatus(response.data);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setError(requestError.response?.data?.error ?? 'Unable to fetch chain status.');
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadStatus();

    return () => {
      active = false;
    };
  }, []);

  const handleNewVote = () => {
    localStorage.removeItem('epic');
    localStorage.removeItem('voteResult');
    navigate('/');
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <section className="panel w-full max-w-3xl p-8 md:p-10">
        <p className="mb-3 inline-flex rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
          {hasVerifiedVote ? 'Voting Complete' : 'Session Incomplete'}
        </p>
        <h1 className="font-display text-4xl font-semibold text-slate-900">
          {hasVerifiedVote ? 'Vote Cast Successfully' : 'No Verified Vote Found'}
        </h1>
        <p className="mt-3 text-base text-slate-600">
          {hasVerifiedVote
            ? 'The vote request has been submitted. The latest chain status is shown below.'
            : 'A successful backend vote response is required before this page can confirm a completed vote.'}
        </p>

        {storedVote ? (
          <div className="mt-6 rounded-2xl border border-green-100 bg-green-50 p-4 text-sm text-green-900">
            <p className="font-semibold">Last vote response</p>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap">{storedVote}</pre>
          </div>
        ) : null}

        <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-950 p-5 text-sm text-slate-100">
          {loading ? (
            <p>Loading chain status...</p>
          ) : error ? (
            <p className="text-rose-300">{error}</p>
          ) : (
            <pre className="overflow-x-auto whitespace-pre-wrap">{JSON.stringify(chainStatus, null, 2)}</pre>
          )}
        </div>

        <button className="primary-button mt-8" type="button" onClick={handleNewVote}>
          Start New Booth Session
        </button>
      </section>
    </main>
  );
}

export default Result;