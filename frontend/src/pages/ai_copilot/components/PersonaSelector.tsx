import React from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, Shield, Zap } from 'lucide-react';

interface Props {
  selectedPersona: string;
  onSelectPersona: (p: string) => void;
}

export const PersonaSelector: React.FC<Props> = ({ selectedPersona, onSelectPersona }) => {
  const { t } = useTranslation('AICopilot');

  const personas = [
    {
      id: 'smc_master',
      title: t('personas.smc_title'),
      desc: t('personas.smc_desc'),
      icon: <Sparkles size={16} className="text-cyan-400" />,
    },
    {
      id: 'risk_officer',
      title: t('personas.risk_title'),
      desc: t('personas.risk_desc'),
      icon: <Shield size={16} className="text-amber-400" />,
    },
    {
      id: 'scalp_sniper',
      title: t('personas.scalp_title'),
      desc: t('personas.scalp_desc'),
      icon: <Zap size={16} className="text-purple-400" />,
    },
  ];

  return (
    <div className="glass-panel p-4 space-y-2.5">
      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
        {t('personas.title')}
      </span>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
        {personas.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelectPersona(p.id)}
            className={`p-3 rounded-xl border text-right transition-all flex items-start gap-2.5 ${
              selectedPersona === p.id
                ? 'bg-cyan-500/15 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                : 'bg-slate-900/60 border-white/5 hover:border-white/20'
            }`}
          >
            <div className="mt-0.5 shrink-0">{p.icon}</div>
            <div>
              <h4 className="text-xs font-bold text-white">{p.title}</h4>
              <p className="text-[10px] text-slate-400 mt-0.5">{p.desc}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
