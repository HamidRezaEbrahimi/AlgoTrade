import React, { useState } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Sparkles, Search, BookmarkPlus, Zap, CheckCircle2 } from 'lucide-react';
import { DiscoveredPattern, CustomPatternItem } from '../types';
import { SavePatternModal } from './SavePatternModal';

interface Props {
  onPatternSaved?: (pattern: CustomPatternItem) => void;
}

export const PatternDiscoveryTab: React.FC<Props> = ({ onPatternSaved }) => {
  const { t } = useTranslation('AIOptimizer');

  const [symbol, setSymbol] = useState<string>('BTCUSDT');
  const [timeframe, setTimeframe] = useState<string>('1h');
  const [minSamples, setMinSamples] = useState<number>(15);
  const [loading, setLoading] = useState<boolean>(false);
  const [discoveries, setDiscoveries] = useState<DiscoveredPattern[]>([]);
  const [selectedPattern, setSelectedPattern] = useState<DiscoveredPattern | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [savedSuccessMsg, setSavedSuccessMsg] = useState<string | null>(null);

  const handleRunMining = async () => {
    setLoading(true);
    setSavedSuccessMsg(null);
    try {
      const res = await axios.post('/api/ai-optimizer/mine-patterns', {
        symbol,
        timeframe,
        min_samples: minSamples,
      });
      setDiscoveries(res.data?.patterns || []);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  const openSaveModal = (pattern: DiscoveredPattern) => {
    setSelectedPattern(pattern);
    setIsModalOpen(true);
  };

  const handleSaved = (pattern: CustomPatternItem) => {
    setSavedSuccessMsg(`الگوی «${pattern.name_fa}» با موفقیت در کتابخانه ذخیره شد.`);
    if (onPatternSaved) onPatternSaved(pattern);
  };

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="glass-panel p-4 space-y-3 border border-white/10 rounded-2xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-cyan-400" />
            <h3 className="text-xs font-bold text-white">{t('discovery.title')}</h3>
          </div>
          <p className="text-[11px] text-slate-400 hidden md:inline">{t('discovery.desc')}</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-slate-400 mb-1 font-medium">{t('discovery.symbol_label')}</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full bg-slate-950/80 border border-white/10 rounded-xl p-2 text-xs text-white font-mono"
            >
              <option value="BTCUSDT">BTC/USDT (بیت‌کوین)</option>
              <option value="ETHUSDT">ETH/USDT (اتریوم)</option>
              <option value="SOLUSDT">SOL/USDT (سولانا)</option>
              <option value="USDTIRT">USDT/IRT (تتر ریال)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">{t('discovery.timeframe_label')}</label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="w-full bg-slate-950/80 border border-white/10 rounded-xl p-2 text-xs text-white"
            >
              <option value="4h">۴ ساعته (4H)</option>
              <option value="1h">۱ ساعته (1H)</option>
              <option value="15m">۱۵ دقیقه (15M)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">{t('discovery.min_samples_label')}</label>
            <input
              type="number"
              value={minSamples}
              onChange={(e) => setMinSamples(Number(e.target.value))}
              className="w-full bg-slate-950/80 border border-white/10 rounded-xl p-2 text-xs text-white text-center font-mono"
            />
          </div>

          <div className="flex items-end">
            <button
              type="button"
              disabled={loading}
              onClick={handleRunMining}
              className="btn btn-sm btn-primary w-full gap-2 shadow-lg shadow-cyan-500/20 font-bold"
            >
              <Search size={14} />
              <span>{loading ? t('discovery.scanning') : t('discovery.btn_start_scan')}</span>
            </button>
          </div>
        </div>
      </div>

      {savedSuccessMsg && (
        <div className="alert alert-success text-xs py-2 px-4 flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>{savedSuccessMsg}</span>
        </div>
      )}

      {/* Discovered Patterns Table */}
      <div className="glass-panel p-4 space-y-3 border border-white/10 rounded-2xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            <h3 className="text-xs font-bold text-white">{t('discovery.results_title')}</h3>
            <span className="badge badge-accent text-[9px] font-mono">{discoveries.length} الگو</span>
          </div>
        </div>

        {discoveries.length === 0 ? (
          <div className="text-center py-10 text-slate-400 text-xs">
            <p>{t('discovery.empty_state')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table w-full text-xs">
              <thead>
                <tr className="border-b border-white/10 text-slate-400 text-[11px]">
                  <th>{t('discovery.col_pattern')}</th>
                  <th>{t('discovery.col_category')}</th>
                  <th>{t('discovery.col_occurrences')}</th>
                  <th>{t('discovery.col_winrate')}</th>
                  <th>{t('discovery.col_profit_factor')}</th>
                  <th>{t('discovery.col_rr')}</th>
                  <th>{t('discovery.col_confidence')}</th>
                  <th className="text-center">{t('discovery.col_action')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {discoveries.map((p) => (
                  <tr key={p.pattern_id} className="hover:bg-white/5 transition-colors">
                    <td>
                      <div>
                        <span className="font-bold text-slate-200 block text-xs">{p.name_fa}</span>
                        <span className="text-[10px] text-slate-400 line-clamp-1">{p.description_fa}</span>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-primary text-[9px]">{p.category.toUpperCase()}</span>
                    </td>
                    <td className="font-mono text-slate-300">{p.occurrences}</td>
                    <td className="font-mono font-bold text-emerald-400">{p.win_rate}٪</td>
                    <td className="font-mono text-cyan-400">{p.profit_factor}</td>
                    <td className="font-mono text-slate-300">1:{p.avg_risk_reward}</td>
                    <td>
                      <span className="badge badge-accent text-[9px] font-mono">{p.confidence_score}٪</span>
                    </td>
                    <td className="text-center">
                      <button
                        type="button"
                        onClick={() => openSaveModal(p)}
                        className="btn btn-xs btn-primary gap-1 shadow-md shadow-cyan-500/10 font-bold"
                      >
                        <BookmarkPlus size={12} />
                        <span>{t('discovery.btn_save_pattern')}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <SavePatternModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialPattern={selectedPattern}
        onSaved={handleSaved}
      />
    </div>
  );
};
