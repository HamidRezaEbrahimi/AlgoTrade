import React from 'react';
import { useTranslation } from 'react-i18next';
import { Sliders } from 'lucide-react';

interface Props {
  strategyName: string;
  setStrategyName: (val: string) => void;
  strategyKey: string;
  setStrategyKey: (val: string) => void;
  structureTf: string;
  setStructureTf: (val: string) => void;
  entryTf: string;
  setEntryTf: (val: string) => void;
  filterTf: string;
  setFilterTf: (val: string) => void;
}

export const IdentityStep: React.FC<Props> = ({
  strategyName,
  setStrategyName,
  strategyKey,
  setStrategyKey,
  structureTf,
  setStructureTf,
  entryTf,
  setEntryTf,
  filterTf,
  setFilterTf,
}) => {
  const { t } = useTranslation(['StrategyBuilder', 'Common']);

  return (
    <div className="glass-panel p-4 space-y-3.5 border border-white/10 rounded-2xl">
      <div className="flex items-center gap-2 border-b border-white/10 pb-2.5">
        <div className="w-6 h-6 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xs">
          <Sliders size={13} />
        </div>
        <h3 className="text-xs font-bold text-white">{t('step1.title')}</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        <div>
          <label className="block text-slate-300 mb-1 font-medium text-[11px]">{t('step1.name_label')}</label>
          <input
            type="text"
            value={strategyName}
            onChange={(e) => setStrategyName(e.target.value)}
            className="w-full bg-slate-950/80 border border-white/10 rounded-xl p-2 text-xs text-white focus:outline-none focus:border-cyan-500"
          />
        </div>
        <div>
          <label className="block text-slate-300 mb-1 font-medium text-[11px]">{t('step1.key_label')}</label>
          <input
            type="text"
            dir="ltr"
            value={strategyKey}
            onChange={(e) => setStrategyKey(e.target.value)}
            className="w-full bg-slate-950/80 border border-white/10 rounded-xl p-2 text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 pt-1 text-xs">
        <div>
          <label className="block text-slate-400 text-[10px] mb-1 font-medium">{t('step1.tf_structure')}</label>
          <select
            value={structureTf}
            onChange={(e) => setStructureTf(e.target.value)}
            className="w-full bg-slate-950/80 border border-white/10 rounded-xl p-1.5 text-xs text-white"
          >
            <option value="4h">{t('Common:timeframes.4h_desc')}</option>
            <option value="1d">{t('Common:timeframes.1d_desc')}</option>
            <option value="1h">{t('Common:timeframes.1h_desc')}</option>
          </select>
        </div>
        <div>
          <label className="block text-slate-400 text-[10px] mb-1 font-medium">{t('step1.tf_entry')}</label>
          <select
            value={entryTf}
            onChange={(e) => setEntryTf(e.target.value)}
            className="w-full bg-slate-950/80 border border-white/10 rounded-xl p-1.5 text-xs text-white"
          >
            <option value="1h">{t('Common:timeframes.1h_desc')}</option>
            <option value="30m">30M</option>
            <option value="15m">{t('Common:timeframes.15m_desc')}</option>
          </select>
        </div>
        <div>
          <label className="block text-slate-400 text-[10px] mb-1 font-medium">{t('step1.tf_filter')}</label>
          <select
            value={filterTf}
            onChange={(e) => setFilterTf(e.target.value)}
            className="w-full bg-slate-950/80 border border-white/10 rounded-xl p-1.5 text-xs text-white"
          >
            <option value="15m">{t('Common:timeframes.15m_desc')}</option>
            <option value="5m">{t('Common:timeframes.5m_desc')}</option>
            <option value="1m">{t('Common:timeframes.1m_desc')}</option>
          </select>
        </div>
      </div>
    </div>
  );
};
