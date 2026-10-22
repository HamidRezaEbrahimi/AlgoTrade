import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { BrainCircuit, Sparkles, Sliders, Cpu, Shapes } from 'lucide-react';
import { PatternRulesTab } from './components/PatternRulesTab';
import { PatternDiscoveryTab } from './components/PatternDiscoveryTab';
import { StrategyOptimizerTab } from './components/StrategyOptimizerTab';
import { LocalModelHubTab } from './components/LocalModelHubTab';

type TabType = 'rules' | 'discovery' | 'optimizer' | 'local_model';

export const AIOptimizerPage: React.FC = () => {
  const { t } = useTranslation('AIOptimizer');
  const [activeTab, setActiveTab] = useState<TabType>('rules');

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 glass-panel p-4 border border-white/10 rounded-2xl">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <BrainCircuit size={22} className="text-cyan-400" />
            <span>{t('header.title')}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('header.subtitle')}</p>
        </div>
      </div>

      {/* Tab Navigation Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-900/90 p-1.5 rounded-2xl border border-white/10">
        <button
          type="button"
          onClick={() => setActiveTab('rules')}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'rules'
              ? 'bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20 font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Shapes size={15} />
          <span>{t('tabs.rules')}</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('discovery')}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'discovery'
              ? 'bg-amber-500 text-slate-950 shadow-lg shadow-amber-500/20 font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Sparkles size={15} />
          <span>{t('tabs.discovery')}</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('optimizer')}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'optimizer'
              ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/20 font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Sliders size={15} />
          <span>{t('tabs.optimizer')}</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('local_model')}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'local_model'
              ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20 font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Cpu size={15} />
          <span>{t('tabs.local_model')}</span>
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'rules' && <PatternRulesTab />}
      {activeTab === 'discovery' && <PatternDiscoveryTab />}
      {activeTab === 'optimizer' && <StrategyOptimizerTab />}
      {activeTab === 'local_model' && <LocalModelHubTab />}
    </div>
  );
};
