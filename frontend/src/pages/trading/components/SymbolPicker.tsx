import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, X, Layers, Flame } from 'lucide-react';
import { SymbolMeta } from '../types';

interface Props {
  symbols: SymbolMeta[];
  selectedSymbol: string;
  selectedExchange: 'wallex' | 'nobitex' | 'faraz';
  onSelectExchange: (ex: 'wallex' | 'nobitex' | 'faraz') => void;
  onSelectSymbol: (symbol: string) => void;
}

const normalize = (text: string): string => {
  return (text || '')
    .toLowerCase()
    .replace(/ي/g, 'ی')
    .replace(/ك/g, 'ک')
    .replace(/ة/g, 'ه')
    .replace(/آ/g, 'ا')
    .replace(/[\u200B-\u200D\uFEFF]/g, '')
    .trim();
};

export const SymbolPicker: React.FC<Props> = ({
  symbols,
  selectedSymbol,
  selectedExchange,
  onSelectExchange,
  onSelectSymbol,
}) => {
  const { t } = useTranslation('Trading');
  const [quoteFilter, setQuoteFilter] = useState<'all' | 'usdt' | 'tmn'>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filtered = useMemo(() => {
    const q = normalize(searchTerm);
    return symbols.filter((s) => {
      // Quote currency filter
      if (quoteFilter === 'usdt' && s.quote?.toUpperCase() !== 'USDT') return false;
      if (quoteFilter === 'tmn' && !['TMN', 'IRT', 'RLS'].includes(s.quote?.toUpperCase() || '')) return false;

      // Text search
      if (!q) return true;

      const normSymbol = normalize(s.symbol);
      const normName = normalize(s.name);
      const normNameEn = normalize(s.name_en || '');
      const normBase = normalize(s.base || '');

      return (
        normSymbol.includes(q) ||
        normName.includes(q) ||
        normNameEn.includes(q) ||
        normBase.includes(q)
      );
    });
  }, [symbols, quoteFilter, searchTerm]);

  return (
    <div className="glass-panel p-4 space-y-3 border border-white/10 rounded-2xl">
      {/* Exchange Switcher Tabs */}
      <div className="grid grid-cols-3 gap-1 p-1 bg-slate-950/80 rounded-xl border border-white/5 text-[11px]">
        <button
          type="button"
          onClick={() => onSelectExchange('wallex')}
          className={`py-2 rounded-lg text-center transition-all flex items-center justify-center gap-1.5 ${
            selectedExchange === 'wallex'
              ? 'bg-cyan-500 text-slate-950 font-extrabold shadow-md shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Layers size={13} />
          <span>والکس (Wallex)</span>
        </button>
        <button
          type="button"
          onClick={() => onSelectExchange('nobitex')}
          className={`py-2 rounded-lg text-center transition-all flex items-center justify-center gap-1.5 ${
            selectedExchange === 'nobitex'
              ? 'bg-purple-500 text-white font-extrabold shadow-md shadow-purple-500/20'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Flame size={13} />
          <span>نوبیتکس (Nobitex)</span>
        </button>
        <button
          type="button"
          onClick={() => onSelectExchange('faraz')}
          className={`py-2 rounded-lg text-center transition-all flex items-center justify-center gap-1.5 ${
            selectedExchange === 'faraz'
              ? 'bg-amber-500 text-slate-950 font-extrabold shadow-md shadow-amber-500/20'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <span>طلا و فارکس</span>
        </button>
      </div>

      {/* Search Input & Count Badge */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search size={14} className="absolute right-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder={t('symbol_picker.search_placeholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border border-white/10 rounded-xl pr-9 pl-8 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 transition-all"
          />
          {searchTerm && (
            <button
              type="button"
              onClick={() => setSearchTerm('')}
              className="absolute left-2.5 top-2.5 text-slate-400 hover:text-white"
            >
              <X size={14} />
            </button>
          )}
        </div>
        <span className="badge badge-accent text-[10px] font-mono px-2 py-1">
          {filtered.length} نماد
        </span>
      </div>

      {/* Quote Currency Sub-Filter */}
      <div className="grid grid-cols-3 gap-1 text-[10.5px]">
        <button
          type="button"
          onClick={() => setQuoteFilter('all')}
          className={`py-1 rounded-lg text-center transition-all ${
            quoteFilter === 'all' ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/30' : 'text-slate-400 hover:text-white'
          }`}
        >
          همه بازارها
        </button>
        <button
          type="button"
          onClick={() => setQuoteFilter('usdt')}
          className={`py-1 rounded-lg text-center transition-all ${
            quoteFilter === 'usdt' ? 'bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30' : 'text-slate-400 hover:text-white'
          }`}
        >
          جفت تتر (USDT)
        </button>
        <button
          type="button"
          onClick={() => setQuoteFilter('tmn')}
          className={`py-1 rounded-lg text-center transition-all ${
            quoteFilter === 'tmn' ? 'bg-amber-500/20 text-amber-400 font-bold border border-amber-500/30' : 'text-slate-400 hover:text-white'
          }`}
        >
          تومان (TMN/RLS)
        </button>
      </div>

      {/* Scrollable Symbol List */}
      <div className="space-y-1 max-h-[380px] overflow-y-auto pr-1">
        {filtered.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500">
            نمادی با عبارت «{searchTerm}» یافت نشد.
          </div>
        ) : (
          filtered.slice(0, 150).map((s) => {
            const isSelected = selectedSymbol.toUpperCase() === s.symbol.toUpperCase();
            return (
              <button
                key={`${s.exchange}-${s.symbol}`}
                type="button"
                onClick={() => onSelectSymbol(s.symbol)}
                className={`w-full p-2 rounded-xl flex items-center justify-between text-xs transition-all ${
                  isSelected
                    ? 'bg-cyan-500/20 border border-cyan-500/50 text-white font-bold shadow-md shadow-cyan-500/10'
                    : 'bg-slate-900/60 hover:bg-slate-800/80 text-slate-300 border border-transparent'
                }`}
              >
                <div className="flex flex-col text-right">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold font-mono text-white">{s.symbol}</span>
                    <span className="text-[9px] px-1 py-0.2 rounded bg-white/5 text-slate-400">
                      {s.quote || 'USDT'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 line-clamp-1">{s.name}</span>
                </div>
                <div className="flex flex-col text-left font-mono">
                  <span className="font-bold text-slate-200">
                    {s.price > 0 ? s.price.toLocaleString() : '-'}
                  </span>
                  <span
                    className={`text-[10px] font-bold ${
                      s.change24h >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {s.change24h >= 0 ? `+${s.change24h}%` : `${s.change24h}%`}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};
