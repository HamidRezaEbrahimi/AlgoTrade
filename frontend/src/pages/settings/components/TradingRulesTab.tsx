import React from 'react';
import { useTranslation } from 'react-i18next';
import { Sliders, CheckCircle2 } from 'lucide-react';

export const TradingRulesTab: React.FC = () => {
  const { t } = useTranslation('Trading');

  const rules = [
    t('criteria.crit_1'),
    t('criteria.crit_2'),
    t('criteria.crit_3'),
    t('criteria.crit_4'),
    t('criteria.crit_5'),
    t('criteria.crit_6'),
    t('criteria.crit_7'),
    t('criteria.crit_8'),
  ];

  return (
    <div className="glass-panel p-5 space-y-4 text-xs">
      <div className="flex items-center gap-2 border-b border-white/10 pb-3">
        <Sliders size={18} className="text-purple-400" />
        <h3 className="text-sm font-bold text-white">قوانین و تاییدیه‌های اجباری استراتژی ۸ معیاره</h3>
      </div>

      <p className="text-slate-300 leading-relaxed text-xs">
        سیستم معاملاتی AlgoTrade بر اساس پروتکل تاییدیه ۸ گانه عمل می‌کند و ورود به معامله مستلزم احراز حداقل ۶ شرط از ۸ شرط زیر است:
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
        {rules.map((rule, idx) => (
          <div key={idx} className="p-3 rounded-xl bg-slate-900/60 border border-white/5 flex items-center gap-2">
            <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
            <span className="text-slate-200 text-xs">{rule}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
