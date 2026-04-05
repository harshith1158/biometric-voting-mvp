import { motion } from 'framer-motion';

export default function CandidateCard({ candidate, isSelected, onSelect }) {
  const imageSrc = candidate.image || 'https://via.placeholder.com/300x200';
  const partyLogo = candidate.logo || 'https://via.placeholder.com/40';
  const isNota = String(candidate.name || '').toUpperCase() === 'NOTA';

  if (isNota) {
    return (
      <motion.div
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.98 }}
        onClick={onSelect}
        className={`rounded-xl p-4 text-center cursor-pointer transition-all duration-300 ease-in-out border-2 bg-white/5 backdrop-blur-md hover:shadow-xl ${
          isSelected
            ? 'bg-yellow-500/20 border-yellow-400 shadow-lg'
            : 'bg-yellow-500/10 border-yellow-500/40 hover:shadow-lg'
        }`}
      >
        <h2 className="font-bold text-lg text-yellow-200">NOTA</h2>
        <p className="text-sm text-yellow-100">None of the Above</p>
      </motion.div>
    );
  }

  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.98 }}
      onClick={onSelect}
      className={`bg-white/5 border border-white/10 backdrop-blur-md shadow-lg hover:shadow-xl rounded-xl p-4 cursor-pointer transition-all duration-300 ease-in-out hover:scale-105 ${
        isSelected ? 'ring-2 ring-green-400 border-green-400/50' : ''
      }`}
    >
      <div className="overflow-hidden rounded-lg bg-white/10">
        <img
          src={imageSrc}
          alt={`${candidate.name} portrait`}
          className="w-full h-44 object-contain transition duration-300 hover:scale-105"
          onError={(e) => {
            e.currentTarget.src = 'https://via.placeholder.com/300x200';
          }}
        />
      </div>

      <div className="flex items-center justify-between mt-2">
        <h2 className="text-lg font-bold text-white">{candidate.name}</h2>
        <img
          src={partyLogo}
          alt={`${candidate.party} logo`}
          className="w-8 h-8 rounded-full"
          onError={(e) => {
            e.currentTarget.src = 'https://via.placeholder.com/40';
          }}
        />
      </div>

      <p className="text-orange-300 font-medium">{candidate.party}</p>
      <p className="text-sm text-gray-300">{candidate.state}</p>
    </motion.div>
  );
}
