import React from 'react';
import { useTranslation } from 'react-i18next';
import { Shield } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

interface Props {
  slType: string;
  setSlType: (val: string) => void;
  minRiskReward: number;
  setMinRiskReward: (val: number) => void;
  tp1Ratio: number;
  setTp1Ratio: (val: number) => void;
  tp2Ratio: number;
  setTp2Ratio: (val: number) => void;
}

export const ExitRiskLayer: React.FC<Props> = ({
  slType,
  setSlType,
  minRiskReward,
  setMinRiskReward,
  tp1Ratio,
  setTp1Ratio,
  tp2Ratio,
  setTp2Ratio,
}) => {
  const { t } = useTranslation(['StrategyBuilder', 'Common']);

  return (
    <div className="glass-panel p-4 space-y-4 border border-white/10 rounded-2xl">
      <div className="flex items-center gap-2 border-b border-white/10 pb-2.5">
        <div className="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-xs">
          <Shield size={13} />
        </div>
        <h3 className="text-xs font-bold text-white">{t('layer4.title')}</h3>
        <InfoTooltip
          title="مدیریت خروج و ریسک معاملاتی"
          text="تنظیم دقیق نقطه حد ضرر، حداقل سود به ریسک مجاز، خروج پله‌ای در تارگت اول و فعال‌سازی ترلینگ استاپ در تارگت دوم."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* Stop Loss Mode */}
        <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <span className="font-bold text-slate-200">{t('layer4.sl_title')}</span>
              <InfoTooltip
                title="محل قرارگیری استاپ‌لاس"
                text="کف سوئینگ قبلی پرایس‌اکشن با حاشیه امن ۰.۱۵٪ یا بر اساس ۱.۵ برابر ضریب نوسان ATR."
              />
            </div>
          </div>
          <select
            value={slType}
            onChange={(e) => setSlType(e.target.value)}
            className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-xs text-white"
          >
            <option value="swing_low">{t('layer4.sl_swing')}</option>
            <option value="atr_dynamic">{t('layer4.sl_atr')}</option>
          </select>
        </div>

        {/* Min R:R Ratio */}
        <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <span className="font-bold text-slate-200">{t('layer4.min_rr')}</span>
              <InfoTooltip
                title="حداقل نسبت سود به ریسک (R:R)"
                text="سیگنال‌هایی که نسبت سود به ریسک کمتر از این مقدار داشته باشند به طور خودکار توسط موتور فیلتر می‌شوند."
              />
            </div>
            <span className="text-[10px] text-amber-400 font-mono" dir="ltr">1 : {minRiskReward}</span>
          </div>
          <input
            type="number"
            step="0.1"
            value={minRiskReward}
            onChange={(e) => setMinRiskReward(Number(e.target.value))}
            className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-xs text-white text-center font-mono"
          />
        </div>
      </div>

      {/* Target 1 and Target 2 Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <span className="font-bold text-emerald-400">{t('layer4.tp1_title')}</span>
              <InfoTooltip
                title="تارگت اول (TP1)"
                text="با لمس این تارگت، استاپ‌لاس فوراً به نقطه ورود منتقل می‌شود تا معامله کاملاً ریسک‌فری (Risk-Free) گردد."
              />
            </div>
            <span className="text-[10px] text-emerald-400 font-mono" dir="ltr">{tp1Ratio} R</span>
          </div>
          <input
            type="number"
            step="0.1"
            value={tp1Ratio}
            onChange={(e) => setTp1Ratio(Number(e.target.value))}
            className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-xs text-white text-center font-mono"
          />
          <span className="text-[10px] text-slate-400 block">{t('layer4.tp1_breakeven')}</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <span className="font-bold text-cyan-400">{t('layer4.tp2_title')}</span>
              <InfoTooltip
                title="تارگت دوم (TP2)"
                text="با رسیدن به این هدف، ۵۰٪ سود تسویه شده و ترلینگ استاپ برای ادامه شکار روند تا بالاترین سطوح فعال می‌شود."
              />
            </div>
            <span className="text-[10px] text-cyan-400 font-mono" dir="ltr">{tp2Ratio} R</span>
          </div>
          <input
            type="number"
            step="0.1"
            value={tp2Ratio}
            onChange={(e) => setTp2Ratio(Number(e.target.value))}
            className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-xs text-white text-center font-mono"
          />
          <span className="text-[10px] text-slate-400 block">{t('layer4.tp2_trailing')}</span>
        </div>
      </div>
    </div>
  );
};
