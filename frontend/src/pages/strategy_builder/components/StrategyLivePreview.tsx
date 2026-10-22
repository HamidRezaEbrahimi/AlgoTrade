import React from 'react';
import { ShieldCheck, Zap, Bot, TrendingUp, Compass, Activity } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

interface Props {
  strategyName: string;
  strategyKey: string;
  structureTf: string;
  entryTf: string;
  filterTf: string;
  minScore: number;
  minRiskReward: number;
  tp1Ratio: number;
  tp2Ratio: number;
  chkAiConfirmation: boolean;
  activePatternsCount: number;
}

export const StrategyLivePreview: React.FC<Props> = ({
  strategyName,
  strategyKey,
  structureTf,
  entryTf,
  filterTf,
  minScore,
  minRiskReward,
  tp1Ratio,
  tp2Ratio,
  chkAiConfirmation,
  activePatternsCount,
}) => {
  return (
    <div className="glass-panel p-3.5 space-y-2.5 border border-cyan-500/30 bg-gradient-to-b from-slate-900/90 via-slate-900/80 to-cyan-950/20 shadow-xl shadow-cyan-950/20 rounded-2xl h-full flex flex-col justify-between">
      {/* Header with Pulse indicator & Tooltip */}
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
          <h3 className="text-xs font-extrabold text-white flex items-center gap-1">
            <Activity size={13} className="text-cyan-400" />
            <span>پیش‌نمایش زنده پیکربندی</span>
          </h3>
          <InfoTooltip
            title="پیش‌نمایش تله‌متری زنده"
            text="این بخش تمامی تنظیمات و خروجی تحلیلی استراتژی را به صورت آنی و همگام با تغییرات فرم نمایش می‌دهد."
          />
        </div>
        <span className="badge badge-accent text-[9px] font-mono" dir="ltr">
          {strategyKey || 'custom_strat'}
        </span>
      </div>

      {/* Strategy Active Name */}
      <div className="bg-slate-950/70 px-2.5 py-1.5 rounded-xl border border-white/5 flex items-center justify-between">
        <span className="text-[10px] text-slate-400 font-medium">ستاپ فعال:</span>
        <h4 className="text-xs font-bold text-cyan-300 line-clamp-1">
          {strategyName || 'استراتژی ترکیبی'}
        </h4>
      </div>

      {/* Multi-TF Badges (LTR for clean English timeframes) */}
      <div className="grid grid-cols-3 gap-1.5" dir="ltr">
        <div className="p-1.5 rounded-xl bg-slate-950/80 border border-white/5 text-center">
          <span className="text-[8.5px] text-slate-400 block">4H (Trend)</span>
          <span className="font-bold text-cyan-400 text-xs">{structureTf.toUpperCase()}</span>
        </div>
        <div className="p-1.5 rounded-xl bg-slate-950/80 border border-white/5 text-center">
          <span className="text-[8.5px] text-slate-400 block">1H (Entry)</span>
          <span className="font-bold text-amber-400 text-xs">{entryTf.toUpperCase()}</span>
        </div>
        <div className="p-1.5 rounded-xl bg-slate-950/80 border border-white/5 text-center">
          <span className="text-[8.5px] text-slate-400 block">15M (Filter)</span>
          <span className="font-bold text-purple-400 text-xs">{filterTf.toUpperCase()}</span>
        </div>
      </div>

      {/* Live Metrics Grid */}
      <div className="grid grid-cols-2 gap-1.5 text-xs">
        <div className="p-2 rounded-xl bg-slate-950/60 border border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Zap size={11} className="text-amber-400" />
            <span className="text-[9.5px] text-slate-400">الگوها:</span>
          </div>
          <span className="text-xs font-bold text-white font-mono">{activePatternsCount} الگو</span>
        </div>

        <div className="p-2 rounded-xl bg-slate-950/60 border border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-1">
            <TrendingUp size={11} className="text-emerald-400" />
            <span className="text-[9.5px] text-slate-400">امتیاز ورود:</span>
          </div>
          <span className="text-xs font-bold text-emerald-400 font-mono" dir="ltr">
            {minScore} / 8
          </span>
        </div>

        <div className="p-2 rounded-xl bg-slate-950/60 border border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Compass size={11} className="text-cyan-400" />
            <span className="text-[9.5px] text-slate-400">حداقل R:R:</span>
          </div>
          <span className="text-xs font-bold text-cyan-400 font-mono" dir="ltr">
            1 : {minRiskReward}
          </span>
        </div>

        <div className="p-2 rounded-xl bg-slate-950/60 border border-white/5 flex items-center justify-between">
          <span className="text-[9.5px] text-slate-400">تارگت‌ها:</span>
          <span className="text-[9.5px] text-emerald-400 font-mono font-bold" dir="ltr">
            {tp1Ratio}R | {tp2Ratio}R
          </span>
        </div>
      </div>

      {/* AI Gate & Risk Footer */}
      <div className="flex items-center justify-between gap-1.5 pt-0.5">
        <div
          className={`flex-1 p-1.5 rounded-xl border flex items-center justify-between text-[9.5px] ${
            chkAiConfirmation
              ? 'bg-cyan-950/40 border-cyan-500/40 text-cyan-300'
              : 'bg-slate-950/40 border-white/5 text-slate-400'
          }`}
        >
          <div className="flex items-center gap-1">
            <Bot size={12} className={chkAiConfirmation ? 'text-cyan-400' : 'text-slate-500'} />
            <span>دروازه هوش مصنوعی</span>
          </div>
          <span className="font-bold">{chkAiConfirmation ? 'فعال ✓' : 'غیرفعال'}</span>
        </div>

        <div className="p-1.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 flex items-center gap-1 text-emerald-300 text-[9.5px]">
          <ShieldCheck size={12} className="text-emerald-400" />
          <span>ریسک ۱٪</span>
        </div>
      </div>
    </div>
  );
};
