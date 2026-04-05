import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Login() {
  const [epic, setEpic] = useState(localStorage.getItem('epic') ?? '');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (event) => {
    event.preventDefault();

    const value = epic.trim().toUpperCase();
    if (!value) {
      setError('Enter an EPIC ID to continue.');
      return;
    }

    localStorage.setItem('epic', value);
    localStorage.removeItem('voteResult');
    setError('');
    navigate('/fingerprint');
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <section className="panel w-full max-w-xl p-8 md:p-10">
        <div className="mb-8">
          <p className="mb-3 inline-flex rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
            TRUE VOTE Booth Terminal
          </p>
          <h1 className="font-display text-4xl font-semibold text-slate-900 md:text-5xl">
            Authenticate voter by EPIC ID
          </h1>
          <p className="mt-3 text-base text-slate-600">
            Start the booth flow by entering the voter&apos;s EPIC number. Fingerprint verification in the next step requires live scanner capture.
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-semibold uppercase tracking-[0.18em] text-slate-500" htmlFor="epic">
            EPIC ID
          </label>
          <input
            id="epic"
            className="input-shell"
            placeholder="Enter EPIC ID"
            value={epic}
            onChange={(event) => setEpic(event.target.value)}
          />
          {error ? <p className="text-sm font-medium text-rose-600">{error}</p> : null}
          <button className="primary-button w-full" type="submit">
            Continue to Fingerprint
          </button>
        </form>
      </section>
    </main>
  );
}

export default Login;