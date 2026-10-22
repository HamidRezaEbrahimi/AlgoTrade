import React, { useState, useMemo, useEffect } from 'react';
import axios from 'axios';
import { Search, X, Layers, Flame, TrendingUp, TrendingDown, Coins } from 'lucide-react';
import { SymbolMeta } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  symbols: SymbolMeta[];
  selectedSymbol: string;
  selectedExchange: 'wallex' | 'nobitex' | 'faraz';
  onSelectExchange: (ex: 'wallex' | 'nobitex' | 'faraz') => void;
  onSelectSymbol: (symbol: string) => void;
}

const normalize = (text: string): string => {
  return (text || '')
    .toLowerCase()
    .replace(/ي|ئ/g, 'ی')
    .replace(/ك/g, 'ک')
    .replace(/ة/g, 'ه')
    .replace(/آ|أ|إ/g, 'ا')
    .replace(/[\u200B-\u200D\uFEFF]/g, '')
    .trim();
};

const normalizePhonetic = (text: string): string => {
  return normalize(text)
    .replace(/ث/g, 'ت')
    .replace(/ص/g, 'س')
    .replace(/ذ|ض|ظ/g, 'ز')
    .replace(/ط/g, 'ت')
    .replace(/ح/g, 'ه');
};

export const SymbolSearchModal: React.FC<Props> = ({
  isOpen,
  onClose,
  symbols,
  selectedSymbol,
  selectedExchange,
  onSelectExchange,
  onSelectSymbol,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [quoteFilter, setQuoteFilter] = useState<'all' | 'usdt' | 'tmn'>('all');
  const [dynamicFarazSymbols, setDynamicFarazSymbols] = useState<SymbolMeta[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Live dynamic search for Faraz symbols across entire TSE & Forex catalog
  useEffect(() => {
    if (selectedExchange !== 'faraz' || !searchTerm.trim()) {
      setDynamicFarazSymbols([]);
      setIsSearching(false);
      return;
    }
    setIsSearching(true);
    const timer = setTimeout(async () => {
      try {
        const queryTerm = searchTerm.trim();
        const res = await axios.get('/api/market/symbols', {
          params: { exchange: 'faraz', query: queryTerm },
        });
        if (res.data && Array.isArray(res.data) && res.data.length > 0) {
          setDynamicFarazSymbols(res.data);
        } else {
          // If typed with 'ت' instead of 'ث' (e.g. تشاهد), try fallback
          const phoneticFallback = queryTerm.replace(/ت/g, 'ث');
          if (phoneticFallback !== queryTerm) {
            const fallbackRes = await axios.get('/api/market/symbols', {
              params: { exchange: 'faraz', query: phoneticFallback },
            });
            if (fallbackRes.data && Array.isArray(fallbackRes.data)) {
              setDynamicFarazSymbols(fallbackRes.data);
            }
          }
        }
      } catch {
        // Fallback
      } finally {
        setIsSearching(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchTerm, selectedExchange]);

  const allSymbols = useMemo(() => {
    if (selectedExchange === 'faraz' && dynamicFarazSymbols.length > 0) {
      const merged = [...dynamicFarazSymbols];
      const seen = new Set(merged.map((s) => s.symbol.toUpperCase()));
      for (const s of symbols) {
        if (!seen.has(s.symbol.toUpperCase())) {
          merged.push(s);
        }
      }
      return merged;
    }
    return symbols;
  }, [symbols, dynamicFarazSymbols, selectedExchange]);

  const filteredSymbols = useMemo(() => {
    const rawQ = searchTerm.trim();
    if (!rawQ) {
      return allSymbols.filter((s) => {
        if (quoteFilter === 'usdt' && !['USDT', 'USD'].includes(s.quote?.toUpperCase() || '')) return false;
        if (quoteFilter === 'tmn' && !['TMN', 'IRT', 'RLS'].includes(s.quote?.toUpperCase() || '')) return false;
        return true;
      });
    }

    const q = normalize(rawQ);
    const qPhonetic = normalizePhonetic(rawQ);

    return allSymbols.filter((s) => {
      // Quote currency filter
      if (quoteFilter === 'usdt' && !['USDT', 'USD'].includes(s.quote?.toUpperCase() || '')) {
        return false;
      }
      if (
        quoteFilter === 'tmn' &&
        !['TMN', 'IRT', 'RLS'].includes(s.quote?.toUpperCase() || '')
      ) {
        return false;
      }

      // Exact / standard match
      const normSymbol = normalize(s.symbol);
      const normName = normalize(s.name);
      const normNameEn = normalize(s.name_en || '');
      const normBase = normalize(s.base || '');

      if (
        normSymbol.includes(q) ||
        normName.includes(q) ||
        normNameEn.includes(q) ||
        normBase.includes(q)
      ) {
        return true;
      }

      // Phonetic match (e.g. تشاهد -> ثشاهد)
      const phName = normalizePhonetic(s.name);
      const phBase = normalizePhonetic(s.base || '');
      return phName.includes(qPhonetic) || phBase.includes(qPhonetic);
    });
  }, [allSymbols, quoteFilter, searchTerm]);

  if (!isOpen) return null;

  const formatPrice = (val?: number) => {
    if (!val || val === 0) return '---';
    if (val < 2.0) return val.toFixed(4);
    return val >= 1000 ? val.toLocaleString() : val.toFixed(2);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in select-none">
      <div className="relative w-full max-w-2xl bg-[#0c1220] border border-white/15 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-[#090d16]">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Search size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">جستجوی نماد و بازارها</h2>
              <p className="text-xs text-slate-400">
                انتخاب جفت‌ارزهای معاملاتی از والکس، نوبیتکس و فراز (فارکس، طلا و بورس تهران)
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Exchange Tabs & Search Input */}
        <div className="p-4 space-y-3 bg-[#0d1322]/80 border-b border-white/10">
          {/* Exchange Switcher */}
          <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-950/90 rounded-xl border border-white/5 text-xs font-bold">
            <button
              type="button"
              onClick={() => {
                onSelectExchange('wallex');
                setSearchTerm('');
              }}
              className={`py-2 rounded-lg flex items-center justify-center gap-2 transition-all ${
                selectedExchange === 'wallex'
                  ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20 font-black'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Layers size={14} />
              <span>والکس (Wallex)</span>
            </button>
            <button
              type="button"
              onClick={() => {
                onSelectExchange('nobitex');
                setSearchTerm('');
              }}
              className={`py-2 rounded-lg flex items-center justify-center gap-2 transition-all ${
                selectedExchange === 'nobitex'
                  ? 'bg-purple-500 text-white shadow-md shadow-purple-500/20 font-black'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Flame size={14} />
              <span>نوبیتکس (Nobitex)</span>
            </button>
            <button
              type="button"
              onClick={() => {
                onSelectExchange('faraz');
                setSearchTerm('');
              }}
              className={`py-2 rounded-lg flex items-center justify-center gap-2 transition-all ${
                selectedExchange === 'faraz'
                  ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20 font-black'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Coins size={14} />
              <span>فراز (بورس، طلا و فارکس)</span>
            </button>
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search size={16} className={`absolute right-3.5 top-3 ${isSearching ? 'text-amber-400 animate-spin' : 'text-slate-400'}`} />
            <input
              type="text"
              autoFocus
              placeholder="جستجوی نماد بورس، طلا یا فارکس (مثال: ثشاهد, وبملت, فولاد, EURUSD, طلا)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-white/15 rounded-xl pr-10 pl-9 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 transition-all font-medium"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                className="absolute left-3 top-3 text-slate-400 hover:text-white"
              >
                <X size={15} />
              </button>
            )}
          </div>

          {/* Quote Currency Badges */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 text-[11px]">پایه معامله:</span>
            {(['all', 'usdt', 'tmn'] as const).map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuoteFilter(q)}
                className={`px-3 py-1 rounded-lg font-bold transition-all ${
                  quoteFilter === q
                    ? 'bg-white/20 text-white border border-white/20'
                    : 'bg-white/5 text-slate-400 hover:text-white border border-white/5'
                }`}
              >
                {q === 'all' ? 'همه بازارها' : q === 'usdt' ? 'دلار / تتر (USD/USDT)' : 'تومان / ریال (TMN/RLS)'}
              </button>
            ))}
            <span className="mr-auto text-[11px] text-slate-400 font-mono">
              {filteredSymbols.length} نماد موجود
            </span>
          </div>
        </div>

        {/* Symbols List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar max-h-[50vh]">
          {filteredSymbols.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs">
              {isSearching ? 'در حال جستجو در نمادهای فراز...' : 'هیچ نمادی با عبارت جستجو شده پیدا نشد.'}
            </div>
          ) : (
            filteredSymbols.map((s) => {
              const isSelected = s.symbol.toUpperCase() === selectedSymbol.toUpperCase();
              const isPositive = (s.change24h ?? 0) >= 0;
              return (
                <button
                  key={s.symbol}
                  type="button"
                  onClick={() => {
                    onSelectSymbol(s.symbol);
                    onClose();
                  }}
                  className={`w-full flex items-center justify-between p-3 rounded-xl transition-all ${
                    isSelected
                      ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 shadow-sm'
                      : 'hover:bg-white/5 text-slate-300 hover:text-white border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex flex-col text-right">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm font-mono">{s.symbol}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-slate-400 uppercase font-mono">
                          {s.quote}
                        </span>
                      </div>
                      <span className="text-xs text-slate-400 mt-0.5">{s.name}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-left font-mono">
                    <div className="flex flex-col items-end">
                      <span className="text-sm font-bold text-white">
                        {s.price > 0 ? (s.quote === 'USD' ? `$${formatPrice(s.price)}` : `${formatPrice(s.price)} ${s.quote}`) : 'فید فراز'}
                      </span>
                      {s.price > 0 && (
                        <div
                          className={`flex items-center gap-1 text-[11px] font-bold ${
                            isPositive ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {isPositive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                          <span>{s.change24h ? `${s.change24h > 0 ? '+' : ''}${s.change24h.toFixed(2)}%` : '0.00%'}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
