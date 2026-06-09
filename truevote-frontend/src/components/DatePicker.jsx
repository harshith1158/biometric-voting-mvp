import { useState, useRef, useEffect } from 'react';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];
const DAY_LABELS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

/**
 * Lightweight custom date-picker.
 * Props:
 *   value    – ISO date string "YYYY-MM-DD" or ""
 *   onChange – called with "YYYY-MM-DD" when user picks a day
 *   maxDate  – ISO date string upper bound (e.g. today)
 *   label    – optional label text
 */
export default function DatePicker({ value, onChange, maxDate, label }) {
  const today = new Date();
  const maxD = maxDate ? new Date(maxDate + 'T00:00:00') : today;

  // Derive initial view from current value, defaulting to ~25 years ago
  const initDate = value ? new Date(value + 'T00:00:00') : null;
  const initYear = initDate ? initDate.getFullYear() : Math.min(today.getFullYear() - 25, maxD.getFullYear());
  const initMonth = initDate ? initDate.getMonth() : today.getMonth();

  const [open, setOpen] = useState(false);
  const [viewYear, setViewYear] = useState(initYear);
  const [viewMonth, setViewMonth] = useState(initMonth);
  const containerRef = useRef(null);

  // Sync view when external value changes
  useEffect(() => {
    if (value) {
      const d = new Date(value + 'T00:00:00');
      setViewYear(d.getFullYear());
      setViewMonth(d.getMonth());
    }
  }, [value]);

  // Close on outside click
  useEffect(() => {
    const handleOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  const prevMonth = () => {
    if (viewMonth === 0) { setViewMonth(11); setViewYear((y) => y - 1); }
    else setViewMonth((m) => m - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) { setViewMonth(0); setViewYear((y) => y + 1); }
    else setViewMonth((m) => m + 1);
  };

  const selectDay = (day) => {
    const d = new Date(viewYear, viewMonth, day);
    if (d > maxD) return;
    const iso = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    onChange(iso);
    setOpen(false);
  };

  // Build calendar cells
  const firstDayOfWeek = new Date(viewYear, viewMonth, 1).getDay();
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const cells = Array(firstDayOfWeek).fill(null).concat(
    Array.from({ length: daysInMonth }, (_, i) => i + 1)
  );

  const isDisabled = (day) => new Date(viewYear, viewMonth, day) > maxD;
  const isSelected = (day) => {
    if (!value) return false;
    const sel = new Date(value + 'T00:00:00');
    return sel.getDate() === day && sel.getMonth() === viewMonth && sel.getFullYear() === viewYear;
  };
  const isToday = (day) => {
    return today.getDate() === day && today.getMonth() === viewMonth && today.getFullYear() === viewYear;
  };

  // Year list: maxDate year down to 1940
  const years = [];
  for (let y = maxD.getFullYear(); y >= 1940; y--) years.push(y);

  // Display text
  const displayText = value
    ? (() => {
        const d = new Date(value + 'T00:00:00');
        return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
      })()
    : 'Select date of birth';

  return (
    <div className="relative" ref={containerRef}>
      {label && <label className="text-gray-400 text-sm mb-1 block">{label}</label>}

      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="border border-white/20 bg-white/10 text-white p-3 rounded w-full text-left focus:ring-2 focus:ring-green-400 flex justify-between items-center"
      >
        <span className={value ? 'text-white' : 'text-gray-400'}>{displayText}</span>
        <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </button>

      {/* Calendar panel */}
      {open && (
        <div className="absolute z-50 mt-1 w-full min-w-[280px] bg-gray-900 border border-white/20 rounded-xl shadow-2xl p-4">

          {/* Month / Year nav row */}
          <div className="flex items-center gap-1 mb-3">
            <button
              type="button"
              onClick={prevMonth}
              className="px-2 py-1 text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors text-lg leading-none"
              aria-label="Previous month"
            >
              ‹
            </button>

            <select
              value={viewMonth}
              onChange={(e) => setViewMonth(Number(e.target.value))}
              className="flex-1 bg-gray-800 text-white text-sm rounded px-2 py-1 border border-white/10 focus:outline-none focus:ring-1 focus:ring-green-400"
            >
              {MONTHS.map((m, i) => (
                <option key={m} value={i}>{m}</option>
              ))}
            </select>

            <select
              value={viewYear}
              onChange={(e) => setViewYear(Number(e.target.value))}
              className="w-[4.5rem] bg-gray-800 text-white text-sm rounded px-2 py-1 border border-white/10 focus:outline-none focus:ring-1 focus:ring-green-400"
            >
              {years.map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>

            <button
              type="button"
              onClick={nextMonth}
              className="px-2 py-1 text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors text-lg leading-none"
              aria-label="Next month"
            >
              ›
            </button>
          </div>

          {/* Day-of-week headers */}
          <div className="grid grid-cols-7 mb-1">
            {DAY_LABELS.map((d) => (
              <div key={d} className="text-center text-xs text-gray-500 py-1 font-medium">{d}</div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7 gap-y-0.5">
            {cells.map((day, i) =>
              day === null ? (
                <div key={`blank-${i}`} />
              ) : (
                <button
                  key={day}
                  type="button"
                  disabled={isDisabled(day)}
                  onClick={() => selectDay(day)}
                  className={[
                    'text-sm rounded-lg py-1.5 text-center transition-colors w-full',
                    isDisabled(day)
                      ? 'text-gray-600 cursor-not-allowed'
                      : 'hover:bg-green-500/30 cursor-pointer',
                    isSelected(day)
                      ? 'bg-green-500 text-white font-bold'
                      : isToday(day)
                      ? 'text-green-400 font-semibold'
                      : 'text-gray-200',
                  ].join(' ')}
                >
                  {day}
                </button>
              )
            )}
          </div>

          {/* Clear + Close row */}
          <div className="mt-3 flex justify-between items-center pt-2 border-t border-white/10">
            {value ? (
              <button
                type="button"
                onClick={() => { onChange(''); setOpen(false); }}
                className="text-xs text-red-400 hover:text-red-300 transition-colors"
              >
                Clear
              </button>
            ) : <span />}
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
