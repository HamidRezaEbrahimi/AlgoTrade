import React from 'react';
import { useTranslation } from 'react-i18next';
import { Radar, ArrowUpRight, ArrowDownRight, CheckCircle2 } from 'lucide-react';
import { useMarketStore } from '../../stores/useMarketStore';
import { useAppStore } from '../../stores/useAppStore';

export const OpportunityList: React.FC = () => {
  const { t } = useTranslation('Scanner');
  const { opportunities, setActiveSymbol, isLoadingOpportunities } = useMarketStore();
  const { setActivePage } = useAppStore();

  const handleSelectSymbol = (symbol: string) => {
    setActiveSymbol(symbol);
    setActivePage('trading');
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Radar className="text-cyan-400" size={22} />
            <span>{t('title')}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">{t('subtitle')}</p>
        </div>
      </div>

      {isLoadingOpportunities && opportunities.length === 0 ? (
        <div className="glass-panel p-8 text-center text-xs text-slate-400">
          در حال اسکن زنده بازار و محاسبه شروط پرایس‌اکشن...
        </div>
      ) : opportunities.length === 0 ? (
        <div className="glass-panel p-8 text-center text-xs text-slate-400">
          {t('no_opportunities')}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {opportunities.map((opp) => (
            <div key={opp.symbol} className="glass-panel p-5 glass-panel-hover transition-all">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-white font-mono">{opp.symbol}</span>
                  <span className={`badge ${opp.direction === 'LONG' ? 'badge-bullish' : 'badge-bearish'}`}>
                    {opp.direction === 'LONG' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                    <span>{opp.direction}</span>
                  </span>
                </div>
                <div className="flex items-center gap-1.5 bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-1 rounded-full text-cyan-400 text-xs font-bold font-mono">
                  <CheckCircle2 size={13} />
                  <span>{opp.total_score} / 8</span>
                </div>
              </div>

              <p className="text-xs text-slate-300 mb-4 leading-relaxed bg-white/[0.02] p-2.5 rounded border border-white/5">
                {opp.reason_fa}
              </p>

              <div className="grid grid-cols-3 gap-2 text-xs text-slate-400 mb-4 bg-slate-950/40 p-2.5 rounded-lg">
                <div>
                  <span className="block text-[10px] text-slate-500">{t('entry_price')}</span>
                  <span className="font-mono text-white numeric-ltr">${opp.current_price.toLocaleString()}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-500">{t('stop_loss')}</span>
                  <span className="font-mono text-red-400 numeric-ltr">${opp.stop_loss.toLocaleString()}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-slate-500">{t('risk_reward')}</span>
                  <span className="font-mono text-emerald-400 font-bold numeric-ltr">1:{opp.risk_reward}</span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleSelectSymbol(opp.symbol)}
                className="w-full btn btn-primary text-xs py-2"
              >
                {t('view_chart_and_trade')}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
