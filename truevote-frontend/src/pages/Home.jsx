import { useNavigate } from 'react-router-dom';
import { playClickSound } from '../utils/soundHelpers';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="relative flex flex-col items-center justify-center min-h-[80vh] text-center px-4 transition-all duration-300 ease-in-out">
      <div className="text-center mt-16">

        {/* Main title */}
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-widest leading-tight bg-gradient-to-r from-orange-400 via-white to-green-400 bg-clip-text text-transparent">
          TRUE VOTE
        </h1>

        {/* Divider with subtitle */}
        <div className="flex items-center gap-3 justify-center mt-4 mb-4">
          <span className="h-px w-12 bg-gradient-to-r from-transparent to-blue-500/60" />
          <p className="text-lg md:text-xl font-extrabold tracking-wider bg-gradient-to-r from-orange-400 via-white to-green-400 bg-clip-text text-transparent">
            The Future of Fair and Transparent Voting
          </p>
          <span className="h-px w-12 bg-gradient-to-l from-transparent to-blue-500/60" />
        </div>

        {/* Quote */}
        <blockquote className="mx-auto mt-2 max-w-sm border-l-4 border-orange-500/60 bg-white/5 px-4 py-3 text-left rounded-r-xl">
          <p className="text-sm text-gray-300 italic leading-relaxed">
            "Empowering democracy through secure digital innovation."
          </p>
        </blockquote>

      </div>

      <div className="mt-10 flex flex-col gap-4 w-full max-w-sm">

        {/* ── GENERATE EPIC ID BUTTON — image card, bottom-left on desktop ── */}
        <div
          onClick={() => { playClickSound(); navigate('/register'); }}
          className="group relative w-full h-24 rounded-xl overflow-hidden cursor-pointer
            shadow-lg hover:shadow-[0_0_28px_rgba(255,153,51,0.5)]
            transition-all duration-300 hover:scale-105
            md:absolute md:top-1/2 md:-translate-y-1/2 md:left-8 md:w-56 md:h-32"
        >
          {/* Voter ID card as texture */}
          <img
            src="/images/registration%20image.jpg"
            className="w-full h-full object-cover object-center scale-105"
            alt=""
          />
          {/* Orange brand overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-orange-600/60 via-orange-500/50 to-orange-400/45 group-hover:from-orange-600/50 group-hover:via-orange-500/40 transition duration-300" />
          {/* Shimmer line */}
          <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-black/20" />
          {/* Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-1">
            <span className="text-white font-bold text-sm tracking-wide drop-shadow">Generate EPIC ID</span>
            <span className="text-orange-100 text-[10px] tracking-widest uppercase">Get Your ID →</span>
          </div>
          {/* Bottom accent bar */}
          <div className="absolute bottom-0 inset-x-0 h-[3px] bg-gradient-to-r from-orange-300 via-white to-orange-300 opacity-60 group-hover:opacity-100 transition" />
        </div>

        {/* ── BOOTH BUTTON — image card, bottom-right on desktop ── */}
        <div
          onClick={() => { playClickSound(); navigate('/booth-login'); }}
          className="group relative w-full h-24 rounded-xl overflow-hidden cursor-pointer
            shadow-lg hover:shadow-[0_0_28px_rgba(34,197,94,0.5)]
            transition-all duration-300 hover:scale-105
            md:absolute md:top-1/2 md:-translate-y-1/2 md:right-8 md:w-56 md:h-32"
        >
          {/* Booth image as texture */}
          <img
            src="/images/booth.jpg"
            className="w-full h-full object-cover object-center scale-105"
            alt=""
          />
          {/* Green brand overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-green-600/60 via-green-500/50 to-green-400/45 group-hover:from-green-600/50 group-hover:via-green-500/40 transition duration-300" />
          {/* Shimmer line */}
          <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-black/20" />
          {/* Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-1">
            <span className="text-white font-bold text-sm tracking-wide drop-shadow">Voting Booth</span>
            <span className="text-green-100 text-[10px] tracking-widest uppercase">Ready? →</span>
          </div>
          {/* Bottom accent bar */}
          <div className="absolute bottom-0 inset-x-0 h-[3px] bg-gradient-to-r from-green-300 via-white to-green-300 opacity-60 group-hover:opacity-100 transition" />
        </div>

        {/* ── NEW USER REGISTRATION LINK ── */}
        <p
          onClick={() => { playClickSound(); navigate('/real-register'); }}
          className="text-base text-gray-300 hover:text-white cursor-pointer transition-colors duration-200 text-center underline underline-offset-4 z-20 md:absolute md:top-[68%] md:left-1/2 md:-translate-x-1/2"
        >
          New User? Register
        </p>

        {/* ── ADMIN BUTTON — image card, bottom-center on desktop ── */}
        <div
          onClick={() => { playClickSound(); navigate('/admin-login'); }}
          className="group relative w-full h-24 rounded-xl overflow-hidden cursor-pointer
            shadow-lg hover:shadow-[0_0_28px_rgba(99,102,241,0.5)]
            transition-all duration-300 hover:scale-105
            md:absolute md:bottom-6 md:left-1/2 md:-translate-x-1/2 md:w-60 md:h-28"
        >
          {/* Admin image as texture */}
          <img
            src="/images/admin.jpg"
            className="w-full h-full object-cover object-center scale-105"
            alt=""
          />
          {/* Indigo brand overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/60 via-blue-600/50 to-indigo-500/45 group-hover:from-indigo-600/50 group-hover:via-blue-600/40 transition duration-300" />
          {/* Shimmer line */}
          <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-black/20" />
          {/* Label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-1">
            <span className="text-white font-bold text-sm tracking-wide drop-shadow">Admin Panel</span>
            <span className="text-blue-100 text-[10px] tracking-widest uppercase">Officials</span>
          </div>
          {/* Bottom accent bar */}
          <div className="absolute bottom-0 inset-x-0 h-[3px] bg-gradient-to-r from-blue-300 via-white to-blue-300 opacity-60 group-hover:opacity-100 transition" />
        </div>
      </div>

    </div>
  );
}
