import React from 'react';
import { useTranslation } from 'react-i18next';
import { Activity } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

interface Props {
  rsiMin: number;
  setRsiMin: (val: number) => void;
  rsiMax: number;
  setRsiMax: (val: number) => void;
  chkVolumeMa: boolean;
  setChkVolumeMa: (val: boolean) => void;
  minScore: number;
  setMinScore: (val: number) => void;
}

export const IndicatorLayer: React.FC<Props> = ({
  rsiMin,
  setRsiMin,
  rsiMax,
  setRsiMax,
  chkVolumeMa,
  setChkVolumeMa,
  minScore,
  setMinScore,
}) => {
  const { t } = useTranslation(['StrategyBuilder', 'Common']);

  return (
    <div className="glass-panel p-4 space-y-4 border border-white/10 rounded-2xl">
      <div className="flex items-center gap-2 border-b border-white/10 pb-2.5">
        <div className="w-6 h-6 rounded-lg bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-xs">
          <Activity size={13} />
        </div>
        <h3 className="text-xs font-bold text-white">{t('layer2.title')}</h3>
        <InfoTooltip
          title="فیلترهای اندیکاتوری و امتیازدهی ۸ معیاره"
          text="فیلترهای مکمل برای اطمینان از مومنتوم مناسب قیمت و حجم کافی معاملات سازمانی قبل از ورود."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* RSI Filter */}
        <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <span className="font-bold text-slate-200">{t('layer2.rsi_title')}</span>
              <InfoTooltip
                title="بازه مجاز شاخص RSI(14)"
                text="محدوده مجاز مومنتوم اندیکاتور RSI در تایم‌فریم ورود برای جلوگیری از خرید در سقف‌های اشباع خرید."
              />
            </div>
            <span className="text-[10px] text-cyan-400 font-mono" dir="ltr">{rsiMin} - {rsiMax}</span>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex-1">
              <label className="text-[10px] text-slate-400 block mb-1">حداقل (Min):</label>
              <input
                type="number"
                value={rsiMin}
                onChange={(e) => setRsiMin(Number(e.target.value))}
                className="w-full bg-slate-900 border border-white/10 rounded-lg p-1.5 text-xs text-white text-center font-mono"
              />
            </div>
            <div className="flex-1">
              <label className="text-[10px] text-slate-400 block mb-1">حداکثر (Max):</label>
              <input
                type="number"
                value={rsiMax}
                onChange={(e) => setRsiMax(Number(e.target.value))}
                className="w-full bg-slate-900 border border-white/10 rounded-lg p-1.5 text-xs text-white text-center font-mono"
              />
            </div>
          </div>
          <span className="text-[10px] text-slate-400 block">{t('layer2.rsi_desc')}</span>
        </div>

        {/* Volume Filter */}
        <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="font-bold text-slate-200">{t('layer2.volume_title')}</span>
              <InfoTooltip
                title="فیلتر تایید حجم سازمانی"
                text="حجم کندل تریگر ورود باید از میانگین متحرک ۱۰ دوره (MA10) حجم بالاتر باشد تا ورود نقدینگی نهادی تایید شود."
              />
            </div>
            <p className="text-[10px] text-slate-400">{t('layer2.volume_desc')}</p>
          </div>

          <label className="flex items-center gap-2 p-2 rounded-lg bg-slate-900/90 border border-white/10 cursor-pointer">
            <input
              type="checkbox"
              checked={chkVolumeMa}
              onChange={(e) => setChkVolumeMa(e.target.checked)}
              className="checkbox checkbox-xs checkbox-primary rounded"
            />
            <span className="text-slate-200 text-xs font-bold">{t('layer2.volume_chk')}</span>
          </label>
        </div>
      </div>

      {/* Min Score Selector */}
      <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <span className="text-xs font-bold text-slate-200">{t('layer2.score_title')}</span>
            <InfoTooltip
              title="حدنصاب امتیاز تاییدیه ورود"
              text="سامانه بر اساس ۸ معیار پرایس‌اکشن، ساختار، حجم و اندیکاتور به هر سیگنال امتیاز می‌دهد. حداقل ۶ امتیاز برای ورود الزامی است."
            />
          </div>
          <span className="text-xs font-bold text-emerald-400 font-mono" dir="ltr">{minScore} / 8</span>
        </div>
        <select
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
          className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 text-xs text-white"
        >
          <option value={5}>{t('layer2.score_5')}</option>
          <option value={6}>{t('layer2.score_6')}</option>
          <option value={7}>{t('layer2.score_7')}</option>
          <option value={8}>{t('layer2.score_8')}</option>
        </select>
      </div>
    </div>
  );
};
