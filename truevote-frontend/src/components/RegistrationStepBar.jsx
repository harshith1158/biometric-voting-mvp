const STEPS = [
  { key: 'aadhaar', label: 'Aadhaar' },
  { key: 'otp', label: 'OTP' },
  { key: 'liveness', label: 'Liveness' },
  { key: 'complete', label: 'Complete' },
];

const ORDER = {
  aadhaar: 0,
  otp: 1,
  liveness: 2,
  complete: 3,
};

export default function RegistrationStepBar({ current = 'aadhaar' }) {
  const currentIndex = ORDER[current] ?? 0;

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between gap-2">
        {STEPS.map((step, index) => {
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex;

          return (
            <div key={step.key} className="flex items-center flex-1">
              <div className="flex flex-col items-center w-full">
                <div
                  className={[
                    'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ease-in-out',
                    isCompleted
                      ? 'bg-green-600 text-white'
                      : isActive
                        ? 'bg-blue-700 text-white shadow-lg'
                        : 'bg-slate-200 text-slate-600',
                  ].join(' ')}
                >
                  {index + 1}
                </div>
                <span
                  className={[
                    'mt-2 text-xs font-medium transition-all duration-300 ease-in-out',
                    isActive ? 'text-blue-900' : isCompleted ? 'text-green-700' : 'text-slate-500',
                  ].join(' ')}
                >
                  {step.label}
                </span>
              </div>

              {index < STEPS.length - 1 && (
                <div
                  className={[
                    'h-1 mx-2 rounded-full w-full transition-all duration-300 ease-in-out',
                    index < currentIndex ? 'bg-green-500' : 'bg-slate-200',
                  ].join(' ')}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}