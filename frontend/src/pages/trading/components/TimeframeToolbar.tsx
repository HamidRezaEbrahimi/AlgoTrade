import React from 'react';

interface Props {
  selectedTf: string;
  onSelectTf: (tf: string) => void;
}

export const TimeframeToolbar: React.FC<Props> = ({ selectedTf, onSelectTf }) => {
  const timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'];

  return (
    <div className="flex items-center gap-1 glass-panel p-1 rounded-xl border border-white/10">
      {timeframes.map((tf) => (
        <button
          key={tf}
          type="button"
          onClick={() => onSelectTf(tf)}
          className={`px-3 py-1 rounded-lg text-xs font-bold font-mono transition-all ${
            selectedTf.toLowerCase() === tf.toLowerCase()
              ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          {tf.toUpperCase()}
        </button>
      ))}
    </div>
  );
};
