import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../services/api';

const ASSEMBLIES = [
  'Secunderabad North',
  'Madhapur Central',
  'Warangal Urban',
  'Visakhapatnam South',
  'Vijayawada East',
  'Tirupati Rural',
];

const PARTIES = [
  'Urban Ward 14',
  'Block C / Station 12',
  'Sector 9 / Station 04',
  'Ward 22 / Station 08',
  'Zone 5 / Station 16',
  'Ward 3 / Station 02',
];

const STATES = [
  'Telangana',
  'Andhra Pradesh',
  'Karnataka',
  'Tamil Nadu',
  'Maharashtra',
  'Kerala',
];

const GENDERS = ['Male', 'Female', 'Other'];

function getProfileFromEpic(epic) {
  const source = epic || 'TV0000000';
  const numericSeed = source
    .split('')
    .reduce((sum, character) => sum + character.charCodeAt(0), 0);

  return {
    epic: source,
    electorName: 'Registered Elector',
    relativeName: 'S/O Verified Citizen',
    assembly: ASSEMBLIES[numericSeed % ASSEMBLIES.length],
    pollingStation: PARTIES[numericSeed % PARTIES.length],
    state: STATES[numericSeed % STATES.length],
    gender: GENDERS[numericSeed % GENDERS.length],
    age: 18 + (numericSeed % 47),
    dob: `${String((numericSeed % 28) + 1).padStart(2, '0')}-${String((numericSeed % 12) + 1).padStart(2, '0')}-${1970 + (numericSeed % 35)}`,
    serialNumber: String(1000 + (numericSeed % 9000)),
    partNumber: String(10 + (numericSeed % 90)).padStart(3, '0'),
    voterSince: 2018 + (numericSeed % 8),
  };
}

function Fingerprint() {
  const [scanning, setScanning] = useState(false);
  const [status, setStatus] = useState('Place the voter finger on the scanner to continue.');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const voterProfile = useMemo(() => getProfileFromEpic(localStorage.getItem('epic') ?? ''), []);
  const epicId = localStorage.getItem('epic') ?? '';

  const handleScan = async () => {
    if (scanning) {
      return;
    }

    if (!epicId) {
      setError('EPIC not found. Please start from login.');
      return;
    }

    setScanning(true);
    setError('');
    setStatus('Scanning fingerprint...');

    try {
      const response = await API.post('/fingerprint/capture', { epic_id: epicId });
      if (response?.data?.message !== 'Fingerprint verified') {
        throw new Error('Fingerprint verification failed.');
      }

      setStatus('Fingerprint authenticated. Proceed to ballot.');
      window.setTimeout(() => {
        navigate('/voting');
      }, 350);
    } catch (requestError) {
      const message = requestError?.response?.data?.error || 'Fingerprint capture failed. Please try again.';
      setStatus('Fingerprint authentication failed.');
      setError(message);
      setScanning(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <section className="panel w-full max-w-6xl overflow-hidden p-0 md:p-0">
        <div className="grid lg:grid-cols-[1.1fr_0.9fr]">
          <div className="relative overflow-hidden bg-slate-950 px-6 py-8 text-white md:px-8 md:py-10">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(249,115,22,0.24),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(34,197,94,0.2),transparent_32%),linear-gradient(140deg,rgba(15,23,42,0.98),rgba(30,41,59,0.96))]" />
            <div className="absolute left-0 right-0 top-0 h-2 bg-gradient-to-r from-orange-500 via-white to-green-500" />
            <div className="absolute -right-10 top-14 h-36 w-36 rounded-full border border-white/10 bg-white/5" />
            <div className="absolute -left-12 bottom-10 h-40 w-40 rounded-full border border-white/10 bg-white/[0.03]" />

            <div className="relative">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.35em] text-orange-200/90">
                    Election Commission of India
                  </p>
                  <h1 className="mt-3 text-2xl font-semibold leading-tight md:text-3xl">
                    Elector Photo Identity Card
                  </h1>
                  <p className="mt-2 max-w-md text-sm text-slate-300">
                    Booth verification preview for voter authentication.
                  </p>
                </div>

                <div className="rounded-2xl border border-white/15 bg-white/10 px-3 py-2 text-right backdrop-blur-sm">
                  <p className="text-[10px] uppercase tracking-[0.28em] text-slate-300">Issued</p>
                  <p className="mt-1 text-sm font-semibold text-white">TRUE VOTE</p>
                </div>
              </div>

              <div className="mt-8 overflow-hidden rounded-[30px] border-[3px] border-[#d8c38a] bg-[#fbf6e8] text-slate-900 shadow-2xl">
                <div className="grid h-full grid-rows-[auto_1fr_auto]">
                  <div className="border-b border-[#d9ccb0] bg-[linear-gradient(180deg,#fff7df_0%,#f8ecd0_100%)] px-5 py-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-[#caa85a] bg-[#fff3ce] text-[10px] font-bold uppercase tracking-[0.16em] text-[#9a6a00]">
                          ECI
                        </div>
                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-[#b45309]">भारत निर्वाचन आयोग</p>
                          <p className="mt-1 text-sm font-semibold uppercase tracking-[0.16em] text-[#1e3a8a]">Election Commission of India</p>
                          <p className="mt-1 text-lg font-bold leading-tight text-slate-900">Elector Photo Identity Card</p>
                        </div>
                      </div>

                      <div className="rounded-xl border border-[#d6c8a7] bg-white/70 px-3 py-2 text-right shadow-sm">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">EPIC No.</p>
                        <p className="mt-1 text-base font-bold tracking-[0.22em] text-[#b91c1c]">{voterProfile.epic}</p>
                      </div>
                    </div>

                    <div className="mt-4 h-2 rounded-full bg-gradient-to-r from-[#f97316] via-white to-[#16a34a]" />
                  </div>

                  <div className="relative px-5 py-5">
                    <div className="absolute inset-y-0 right-6 hidden w-36 rounded-full border border-[#d7ccb6] opacity-30 md:block" />
                    <div className="grid gap-5 md:grid-cols-[168px_1fr]">
                      <div>
                        <div className="rounded-[22px] border border-[#cdbf98] bg-white px-3 py-3 shadow-sm">
                          <div className="flex h-44 items-center justify-center rounded-[16px] border border-[#d5d8df] bg-[linear-gradient(180deg,#eef4ff_0%,#ffffff_100%)]">
                            <div className="relative flex h-28 w-24 flex-col items-center justify-center rounded-[14px] border border-slate-300 bg-slate-100 shadow-inner">
                              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-700 text-xl font-bold text-white">
                                {voterProfile.epic.slice(0, 2) || 'TV'}
                              </div>
                              <div className="mt-3 h-1 w-14 rounded-full bg-slate-300" />
                              <div className="mt-2 h-1 w-10 rounded-full bg-slate-200" />
                            </div>
                          </div>
                        </div>

                        <div className="mt-3 rounded-xl border border-[#cfc3a5] bg-[#fff8e7] px-3 py-2 text-center shadow-sm">
                          <p className="text-[10px] uppercase tracking-[0.22em] text-slate-500">Card Status</p>
                          <p className="mt-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#15803d]">Identity Ready For Verification</p>
                        </div>
                      </div>

                      <div className="grid gap-3">
                        <div className="grid gap-x-5 gap-y-3 md:grid-cols-2">
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Name / नाम</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-base font-bold text-slate-900">{voterProfile.electorName}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Father / Mother / Guardian</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.relativeName}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Sex / Gender</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.gender}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Date of Birth</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.dob}</p>
                          </div>
                        </div>

                        <div className="grid gap-x-5 gap-y-3 md:grid-cols-3">
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Age</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.age} Years</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Part No.</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.partNumber}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Serial No.</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.serialNumber}</p>
                          </div>
                        </div>

                        <div>
                          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Assembly Constituency</p>
                          <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.assembly}</p>
                        </div>

                        <div className="grid gap-x-5 gap-y-3 md:grid-cols-2">
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">State</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.state}</p>
                          </div>
                          <div>
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Polling Station</p>
                            <p className="mt-1 border-b border-dotted border-[#bfae88] pb-1 text-sm font-semibold text-slate-800">{voterProfile.pollingStation}</p>
                          </div>
                        </div>

                        <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                          <div className="rounded-xl border border-[#d8ceb6] bg-white/70 px-4 py-3 shadow-sm">
                            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Booth Authentication</p>
                            <p className="mt-1 text-sm font-medium text-slate-700">Eligible voter record loaded for fingerprint verification and ballot access.</p>
                          </div>
                          <div className="flex items-center justify-center rounded-xl border border-dashed border-[#b8aa85] bg-[#fff8e8] px-4 py-3">
                            <div className="flex items-end gap-[2px]">
                              {[24, 34, 18, 38, 28, 36, 16, 32, 22, 30, 18, 40].map((height, index) => (
                                <span
                                  key={index}
                                  className="w-[3px] rounded-full bg-slate-700"
                                  style={{ height }}
                                />
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-[#d9ccb0] bg-[linear-gradient(180deg,#f8ecd0_0%,#f4e6c0_100%)] px-5 py-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Elector Since</p>
                        <p className="mt-1 text-sm font-semibold text-slate-800">{voterProfile.voterSince}</p>
                      </div>
                      <div className="h-px min-w-24 flex-1 bg-gradient-to-r from-transparent via-[#b89d57] to-transparent" />
                      <div className="text-right">
                        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Booth Verification Seal</p>
                        <p className="mt-1 text-xs font-bold uppercase tracking-[0.18em] text-[#166534]">Fingerprint Match Pending</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="px-6 py-8 text-center md:px-10 md:py-12">
            <div className="mx-auto flex max-w-md flex-col items-center">
              <div className="mb-8 flex h-40 w-40 items-center justify-center rounded-full border border-green-200 bg-green-50 shadow-inner">
                <div className={`flex h-28 w-28 items-center justify-center rounded-full border-4 border-green-500 ${scanning ? 'animate-pulseRing' : ''}`}>
                  <span className="text-5xl">◎</span>
                </div>
              </div>

              <p className="mb-3 inline-flex rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-800">
                Fingerprint Verification
              </p>
              <h2 className="font-display text-4xl font-semibold text-slate-900">Match voter identity</h2>
              <p className="mt-4 text-base text-slate-600">{status}</p>
              {error ? <p className="mt-2 text-sm font-medium text-rose-600">{error}</p> : null}

              <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm text-slate-600 shadow-sm">
                <p className="font-semibold uppercase tracking-[0.18em] text-slate-500">Verification Checklist</p>
                <p className="mt-2">EPIC record loaded for booth operator review.</p>
                <p className="mt-1">Fingerprint scan authorizes access to the ballot screen.</p>
              </div>

              <button
                className="primary-button mt-8 min-w-60"
                onClick={handleScan}
                type="button"
                disabled={scanning}
              >
                {scanning ? 'Scanning...' : 'Scan Fingerprint'}
              </button>
            </div>
          </div>
        </div>
      </section>
  );
}

export default Fingerprint;