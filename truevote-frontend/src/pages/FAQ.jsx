import React, { useState } from 'react';

const faqs = [
  {
    question: "How is voter identity verified?",
    answer: "Voters are verified through a multi-step process: (1) Aadhaar-based mock verification simulating UIDAI authentication, (2) Face liveness detection using MediaPipe AI to prevent spoofing, (3) Fingerprint validation against registered biometric datasets."
  },
  {
    question: "Can one person vote multiple times?",
    answer: "No. Each Aadhaar-linked EPIC ID is registered as unique in the system. Once a voter completes the voting process, their EPIC ID is marked as voted, preventing duplicate votes."
  },
  {
    question: "Why can't RD (Registered Device) fingerprints be matched locally?",
    answer: "RD devices provide encrypted biometric data in proprietary format that can only be processed by UIDAI's official servers. Local fingerprint matching is simulated in the prototype, but real systems would require UIDAI authentication APIs."
  },
  {
    question: "How is vote integrity ensured?",
    answer: "TRUE VOTE uses a blockchain-inspired hash chain system where each vote is cryptographically linked to the previous vote. This creates an immutable audit trail that prevents tampering and allows verification of vote counts."
  },
  {
    question: "What biometric data is collected?",
    answer: "The system collects: (1) Face images for liveness detection (processed locally, not stored), (2) Fingerprint IDs from registered datasets for matching, (3) Basic Aadhaar information (name, gender, DOB, state) for verification."
  },
  {
    question: "Is this a real voting system?",
    answer: "No, TRUE VOTE is a research prototype and proof-of-concept. It demonstrates secure voting principles but uses simulated Aadhaar verification and mock fingerprint databases. It is not intended for real elections."
  },
  {
    question: "How does the admin dashboard work?",
    answer: "The admin dashboard provides real-time vote tallies, blockchain chain status verification, tamper attempt monitoring, and vote distribution visualization. Only authorized officials with admin credentials can access it."
  },
  {
    question: "What happens if liveness detection fails?",
    answer: "If the liveness detection fails, the voter is notified and can retry. The system will not proceed to the voting booth until liveness is confirmed. This prevents spoofing attacks using recorded videos or photos."
  },
  {
    question: "Can votes be traced back to voters?",
    answer: "The system is designed for privacy: Votes are linked to EPIC IDs (not names) and stored separately from personal data. The audit trail tracks vote integrity, not voter identity."
  },
  {
    question: "What if I forget my Aadhaar number?",
    answer: "The system requires a valid 12-digit Aadhaar number to begin registration. In a real system, you could use other government IDs. This prototype focuses on Aadhaar-based simulation."
  },
  {
    question: "How long does the voting process take?",
    answer: "Typical flow: Registration (5-10 min) → OTP Verification (2-3 min) → Liveness Check (5-10 sec) → Fingerprint Verification (2-3 sec) → Booth Voting (2-5 min). Total: ~15-30 minutes."
  },
  {
    question: "Is fingerprint data encrypted?",
    answer: "In the prototype, fingerprint dataset IDs are used for matching. In production, biometric data would be encrypted using AES-256 and stored in secure HSM (Hardware Security Module) devices to comply with UIDAI standards."
  }
];

export default function FAQ() {
  const [expanded, setExpanded] = useState(null);

  const toggleExpand = (index) => {
    setExpanded(expanded === index ? null : index);
  };

  return (
    <div className="min-h-screen bg-black text-white p-4 md:p-10 transition-opacity duration-500 opacity-100 ease-in-out">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-extrabold mb-4 bg-gradient-to-r from-orange-400 via-white to-green-400 bg-clip-text text-transparent">
          Frequently Asked Questions
        </h1>
        <p className="text-gray-400 mb-10">
          Everything you need to know about TRUE VOTE's secure voting system
        </p>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-white/5 border border-white/10 rounded-xl backdrop-blur-md overflow-hidden hover:border-white/20 transition"
            >
              <button
                onClick={() => toggleExpand(index)}
                className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-white/5 transition"
              >
                <h2 className="font-semibold text-lg text-white">
                  {faq.question}
                </h2>
                <span className={`text-2xl text-green-400 transition transform ${expanded === index ? 'rotate-180' : ''}`}>
                  +
                </span>
              </button>

              {expanded === index && (
                <div className="px-6 py-4 border-t border-white/10 bg-white/2.5 text-gray-300 leading-relaxed">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-12 bg-green-900/20 border border-green-500/30 rounded-xl p-6 text-center">
          <h3 className="text-xl font-bold text-green-300 mb-2">Still have questions?</h3>
          <p className="text-gray-400">
            Contact the development team at{' '}
            <a
              href="mailto:harshithkumar746@gmail.com"
              className="text-green-400 hover:text-green-300 underline underline-offset-2 transition-colors duration-200"
            >
              harshithkumar746@gmail.com
            </a>
            {' '}or visit the About page to learn more about TRUE VOTE's architecture.
          </p>
        </div>
      </div>
    </div>
  );
}
