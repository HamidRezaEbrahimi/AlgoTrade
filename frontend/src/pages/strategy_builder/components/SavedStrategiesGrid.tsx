import React from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, CheckCircle2 } from 'lucide-react';
import { StrategyItem } from '../types';

interface Props {
  strategies: StrategyItem[];
  loading: boolean;
}

export const SavedStrategiesGrid: React.FC<Props> = ({ strategies, loading }) => {
  const { t, i18n } = useTranslation('StrategyBuilder');
  const isFa = i18n.language === 'fa';

  return (
    <div className="glass-panel p-5 space-y-3">
      <div className="flex items-center gap-2 border-b border-white/10 pb-2.5">
        <Sparkles size={18} className="text-cyan-400" />
        <h3 className="text-sm font-bold text-white">{t('registry.title')}</h3>
      </div>

      {loading ? (
        <p className="text-xs text-slate-400 py-3 text-center">{t('registry.loading')}</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
          {strategies.map((strat) => (
            <div
              key={strat.key}
              className="p-3.5 rounded-xl bg-slate-900/80 border border-white/10 flex flex-col justify-between space-y-2 hover:border-cyan-500/30 transition-all"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="badge badge-primary text-[9px]">
                    {strat.is_builtin ? t('registry.builtin_tag') : t('registry.custom_tag')}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">{strat.key}</span>
                </div>
                <h4 className="text-xs font-bold text-white mt-1.5">
                  {isFa ? strat.name_fa || strat.name_en || strat.key : strat.name_en || strat.name_fa || strat.key}
                </h4>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-bold pt-1 border-t border-white/5">
                <CheckCircle2 size={12} />
                <span>{t('registry.status_active')}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
