import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getCandidates,
  getChainStatus,
} from '../services/api';
import API from '../services/api';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';

const COLORS = ['#1e3a8a', '#16a34a', '#f97316', '#9333ea'];

function getCandidateVoteValue(candidate) {
  return Number(
    candidate?.votes ?? candidate?.vote_count ?? candidate?.voteCount ?? 0
  ) || 0;
}

function hasCandidateVoteField(candidate) {
  return (
    candidate?.votes != null ||
    candidate?.vote_count != null ||
    candidate?.voteCount != null
  );
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [chainStatus, setChainStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [apiConnected, setApiConnected] = useState(null);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [declaring, setDeclaring] = useState(false);

  console.log('[AdminDashboard] Mounted, current state:', { loading, candidates: candidates.length, error });

  const fetchData = async (isInitial = false) => {
    if (isInitial) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError('');

    try {
      console.log('[AdminDashboard] Fetching data...');
      const [candidateResponse, chainResponse] = await Promise.all([
        getCandidates(),
        getChainStatus(),
      ]);

      const candidatePayload = candidateResponse?.data;
      const normalizedCandidates = Array.isArray(candidatePayload)
        ? candidatePayload
        : candidatePayload?.candidates ?? [];

      console.log('[AdminDashboard] Data fetched:', { candidates: normalizedCandidates.length, chain: chainResponse?.data });
      setCandidates(normalizedCandidates);
      setChainStatus(chainResponse?.data ?? null);
      setApiConnected(true);
      setLastUpdated(new Date());
    } catch (requestError) {
      console.error('[AdminDashboard] Fetch error:', requestError);
      setApiConnected(false);
      setError(requestError?.response?.data?.error || 'Failed to load admin dashboard.');
    } finally {
      if (isInitial) {
        setLoading(false);
      } else {
        setRefreshing(false);
      }
    }
  };

  useEffect(() => {
    fetchData(true);

    const interval = setInterval(() => {
      fetchData(false);
      console.log('Auto-refresh dashboard...');
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const data = useMemo(
    () => candidates.map((candidate) => ({
      name: candidate.name,
      value: getCandidateVoteValue(candidate),
    })),
    [candidates]
  );

  const voteDataAvailable = useMemo(
    () => candidates.some((candidate) => hasCandidateVoteField(candidate)),
    [candidates]
  );

  const totalVotes = data.reduce((sum, entry) => sum + entry.value, 0);
  const totalCandidates = candidates.length;
  const chainLength = Number(chainStatus?.length ?? 0);
  const chainValid = Boolean(chainStatus?.valid);
  const votingClosed = Boolean(chainStatus?.voting_closed ?? chainStatus?.closed ?? false);
  const topCandidate = useMemo(() => {
    const normalizedCandidates = candidates.map((candidate) => ({
      ...candidate,
      votes: getCandidateVoteValue(candidate),
    }));

    const sorted = [...normalizedCandidates].sort((a, b) => b.votes - a.votes);

    const topVotes = sorted[0]?.votes || 0;

    const leaders = sorted.filter((c) => c.votes === topVotes);

    let leaderText = '';

    if (leaders.length === 1) {
      leaderText = leaders[0].name;
    } else if (leaders.length > 1) {
      leaderText = `Tie: ${leaders.map((l) => l.name).join(', ')}`;
    } else {
      leaderText = 'No votes yet';
    }

    return leaderText;
  }, [candidates]);

  return (
    <div className="px-4 py-10 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="mx-auto max-w-6xl">
        {error && (
          <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 px-4 py-3">
            <strong>Error:</strong> {error}
          </div>
        )}
        <div className="rounded-[2rem] bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 p-6 md:p-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="inline-flex rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-orange-300">
                Election Commission Console
              </p>
              <h1 className="mt-4 text-3xl font-extrabold text-white md:text-4xl">Admin Dashboard</h1>
              <span className="inline-flex items-center gap-1 rounded-full bg-green-500/20 px-3 py-1 text-xs font-semibold text-green-300">● LIVE</span>
            </div>

            <div className="flex flex-col items-end gap-2">
              <button
                onClick={() => fetchData(false)}
                className="rounded-xl bg-gradient-to-r from-orange-500 to-green-500 px-4 py-2 text-white shadow-lg transition-all duration-300 hover:scale-105"
              >
                Refresh Now
              </button>
              <button
                onClick={() => {
                  localStorage.removeItem('admin');
                  window.location.href = '/';
                }}
                className="rounded-xl bg-red-500 px-4 py-2 text-white shadow-lg transition-all duration-300 hover:scale-105 hover:bg-red-600"
              >
                Logout
              </button>
              <button
                onClick={async () => {
                  setDeclaring(true);
                  try { await API.post('/declare_result'); } catch (_) { /* endpoint may not exist */ }
                  localStorage.setItem('tv_result_declared', 'true');
                  setDeclaring(false);
                  navigate('/result');
                }}
                disabled={declaring}
                className="rounded-xl bg-gradient-to-r from-red-600 to-orange-500 px-4 py-2 text-white shadow-lg transition-all duration-300 hover:scale-105 disabled:opacity-60 font-semibold"
              >
                {declaring ? 'Declaring...' : 'Declare Result'}
              </button>
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-4">
            {lastUpdated ? (
              <p className="text-xs text-gray-400">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </p>
            ) : null}

            {apiConnected === true ? (
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                API Connected
              </span>
            ) : null}

            {apiConnected === false ? (
              <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700">
                API Disconnected
              </span>
            ) : null}

            {!loading && voteDataAvailable ? (
              <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                Vote Data Available
              </span>
            ) : null}

            {!loading && !voteDataAvailable ? (
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                Vote Data Not Available
              </span>
            ) : null}

            {refreshing ? (
              <div className="text-sm text-blue-600">Updating data...</div>
            ) : null}
          </div>

          {error ? (
            <div className="mt-6 rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          ) : null}

          <div className="p-6 rounded-xl text-center shadow-lg bg-gradient-to-r from-green-600/20 to-green-400/10 animate-pulse hover:shadow-xl transition duration-300 ease-in-out mt-6">
            <h2 className="text-lg text-gray-300">🏆 Leading Candidate</h2>
            <p className="text-2xl font-bold text-green-400 mt-2">{topCandidate}</p>
            {votingClosed && (
              <div className="text-xs text-red-400 text-center mt-2">
                🔒 Result Locked
              </div>
            )}
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 space-y-4 md:space-y-0">
            <div className="p-4 bg-white/5 border border-white/10 backdrop-blur-md shadow-lg rounded-xl text-center transition-all duration-300 hover:scale-105">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-300">Total Votes</p>
              <p className="mt-3 text-3xl font-bold text-white">{loading ? '--' : totalVotes}</p>
            </div>

            <div className="p-4 bg-white/5 border border-white/10 backdrop-blur-md shadow-lg rounded-xl text-center transition-all duration-300 hover:scale-105">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-300">🔗 Chain Status</p>
              <p className="mt-3 text-3xl font-bold text-white">{loading ? '--' : chainLength}</p>
              <p className={`mt-2 text-sm font-semibold ${chainValid ? 'text-green-300' : 'text-red-300'}`}>
                {loading ? 'Checking...' : chainValid ? 'Chain valid' : 'Chain invalid'}
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-3xl bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 ease-in-out p-5 hover:scale-[1.01]">
              <div className="flex items-center justify-between gap-4">
                <h2 className="font-bold text-white">Candidate Registry</h2>
                <span className="text-xs text-gray-400">Frontend-only view</span>
              </div>

              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-gray-300">
                      <th className="px-3 py-3 font-semibold">Candidate</th>
                      <th className="px-3 py-3 font-semibold">Party</th>
                      <th className="px-3 py-3 font-semibold">Constituency</th>
                      <th className="px-3 py-3 font-semibold">Votes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td className="px-3 py-4 text-gray-400" colSpan="4">Loading dashboard data...</td>
                      </tr>
                    ) : candidates.length === 0 ? (
                      <tr>
                        <td className="px-3 py-4 text-gray-400" colSpan="4">No candidate data available.</td>
                      </tr>
                    ) : (
                      candidates.map((candidate) => (
                        <tr key={candidate.id} className="border-b border-white/10 last:border-b-0">
                          <td className="px-3 py-4 font-semibold text-white">{candidate.name}</td>
                          <td className="px-3 py-4 text-gray-300">{candidate.party}</td>
                          <td className="px-3 py-4 text-gray-300">{candidate.state}</td>
                          <td className="px-3 py-4 text-white">{getCandidateVoteValue(candidate)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl transition duration-300 ease-in-out p-5 rounded-3xl hover:scale-[1.01]">
              <h2 className="font-bold mb-3 text-white">Vote Distribution</h2>

              <div className="flex justify-center">
                <PieChart width={300} height={300}>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={100}
                    label
                  >
                    {data.map((entry, index) => (
                      <Cell key={`${entry.name}-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>

                  <Tooltip />
                  <Legend />
                </PieChart>
              </div>

              <p className="mt-3 text-xs leading-5 text-gray-400">
                The current API does not expose per-candidate tally fields consistently. The chart renders any returned vote values and falls back to zero otherwise.
              </p>
              {!loading && !voteDataAvailable ? (
                <p className="mt-2 text-xs leading-5 text-amber-300">
                  Candidate vote breakdown is unavailable until vote fields are included in API responses.
                </p>
              ) : null}

              <div className="mt-4">
                {data.map((candidate) => {
                  const percentage = totalVotes > 0 ? (candidate.value / totalVotes) * 100 : 0;
                  return (
                    <div key={candidate.name} className="mb-2">
                      <div className="flex justify-between text-sm text-gray-200">
                        <span>{candidate.name}</span>
                        <span>{candidate.value}</span>
                      </div>

                      <div className="w-full bg-white/10 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-orange-400 to-green-400 h-2 rounded-full shadow-[0_0_12px_rgba(34,197,94,0.45)]"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}