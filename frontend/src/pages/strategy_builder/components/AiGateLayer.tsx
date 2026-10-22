import React from 'react';
import { useTranslation } from 'react-i18next';
import { Bot } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

interface Props {
  chkAiConfirmation: boolean;
  setChkAiConfirmation: (val: boolean) => void;
}

export const AiGateLayer: React.FC<Props> = ({ chkAiConfirmation, setChkAiConfirmation }) => {
  const { t } = useTranslation(['StrategyBuilder', 'Common']);

  return (
    <div className="glass-panel p-4 space-y-3 border border-white/10 rounded-2xl">
      <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xs">
            <Bot size={13} />
          </div>
          <h3 className="text-xs font-bold text-white">{t('layer3.title')}</h3>
          <InfoTooltip
            title="دروازه تایید هوش مصنوعی (AI Copilot Gate)"
            text="هنگام فعال بودن، سیگنال‌های فنی به مدل هوش مصنوعی ارسال شده و تنها در صورت تایید سناریوی نقدینگی و عدم وجود تناقض در تایم‌فریم‌های بالاتر، اجازه ورود صادر می‌گردد."
          />
        </div>
        <span
          className={`badge text-[9px] font-bold ${
            chkAiConfirmation ? 'badge-primary' : 'badge-ghost'
          }`}
        >
          {chkAiConfirmation ? t('layer3.btn_active') : t('layer3.btn_inactive')}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-slate-950/70 border border-white/5">
        <div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            {chkAiConfirmation ? t('layer3.desc_active') : t('layer3.desc_inactive')}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setChkAiConfirmation(!chkAiConfirmation)}
          className={`btn btn-sm shrink-0 transition-all font-bold ${
            chkAiConfirmation
              ? 'btn-primary shadow-lg shadow-cyan-500/20'
              : 'btn-ghost border border-white/10 text-slate-400'
          }`}
        >
          {chkAiConfirmation ? t('layer3.btn_active') : t('layer3.btn_inactive')}
        </button>
      </div>
    </div>
  );
};
