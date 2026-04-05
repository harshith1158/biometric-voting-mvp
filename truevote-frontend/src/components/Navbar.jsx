import { useNavigate } from 'react-router-dom';

export default function Navbar() {
  const navigate = useNavigate();

  return (
    <>
      <header className="sticky top-0 z-50 bg-transparent flex justify-between items-center px-6 py-3 transition-all duration-300 ease-in-out">
        <div
          onClick={() => navigate('/')}
          className="flex items-center gap-3 cursor-pointer hover:scale-105 transition"
        >
          <img
            src="/images/new.jpg"
            className="w-14 h-14 md:w-16 md:h-16 object-contain shrink-0 rounded-full"
            alt="TrueVote Logo"
          />
          <span className="font-bold tracking-wide text-lg text-white">TRUE VOTE</span>
        </div>

        <div className="flex gap-6 text-sm text-gray-300">
          <span className="cursor-pointer hover:text-white hover:underline hover:underline-offset-4 transition" onClick={() => navigate('/')}>Home</span>
          <span className="cursor-pointer hover:text-white hover:underline hover:underline-offset-4 transition" onClick={() => navigate('/about')}>About</span>
          <span className="cursor-pointer hover:text-white hover:underline hover:underline-offset-4 transition" onClick={() => navigate('/faq')}>FAQs</span>
          <span className="cursor-pointer hover:text-white hover:underline hover:underline-offset-4 transition" onClick={() => navigate('/admin-login')}>Admin</span>
        </div>
      </header>
    </>
  );
}
