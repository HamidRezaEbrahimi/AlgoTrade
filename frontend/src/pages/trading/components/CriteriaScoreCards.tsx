import React from 'react';
import {
  Boxes,
  Shield,
  TrendingUp,
  TrendingDown,
  Search,
  ArrowUpRight,
  ArrowDownRight,
  Sliders,
  Eye,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { CriteriaResult, PatternMarker } from '../types';
import { formatDualDateTime } from '../../../utils/dateFormatter';
import { WaveProgressTracker } from './WaveProgressTracker';

interface Props {
  analysis: CriteriaResult;
  currentPrice?: number;
  selectedPatternId?: string | null;
  onFocusPattern?: (time: number, pattern?: PatternMarker) => void;
  onOpenSettings?: () => void;
  onInspectPattern?: (pattern: PatternMarker) => void;
}

export const CriteriaScoreCards: React.FC<Props> = ({
  analysis,
  selectedPatternId,
  onFocusPattern,
  onOpenSettings,
  onInspectPattern,
}) => {
  const signal = analysis.trade_setup?.signal || 'WAIT';
  const isWait = signal === 'WAIT';
  const isBuy = signal === 'BUY';
  const detectedPatterns = analysis?.detected_patterns || [];
  const displayPatterns = [...detectedPatterns].sort((a: PatternMarker, b: PatternMarker) => b.time - a.time);

  // Active pattern priority: Selected > Live PRZ Entry > Confirmed Wave > Developing Wave
  const activePattern = selectedPatternId
    ? displayPatterns.find((p) => p.id === selectedPatternId) || null
    : (
        displayPatterns.find((p) => Boolean((p as any).is_developing) && (p as any).trade_setup?.is_live_entry) ||
        displayPatterns.find((p) => !Boolean((p as any).is_developing) && p.points && p.points.length >= 4) ||
        displayPatterns.find((p) => Boolean((p as any).is_developing) && p.points && p.points.length >= 4) ||
        (displayPatterns.length > 0 ? displayPatterns[0] : null)
      );

  const patternProbability = activePattern?.pattern_probability ?? analysis?.pattern_probability ?? 0;
  const tradeWinProbability = activePattern?.trade_win_probability ?? analysis?.trade_win_probability ?? 0;
  const progressiveStages = activePattern?.progressive_stages ?? analysis?.progressive_stages ?? [];
  const isDeveloping = Boolean((activePattern as any)?.is_developing);
  const stageLabel = (activePattern as any)?.stage_label ?? analysis?.stage_label;

  const formatPrice = (val?: number) => {
    if (val === undefined || val === null || val === 0) return '---';
    if (val >= 1000) return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
    if (val < 0.001) return val.toFixed(8);
    if (val < 0.1) return val.toFixed(6);
    if (val < 10) return val.toFixed(5);
    if (val < 500) return val.toFixed(3);
    return val.toFixed(2);
  };

  return (
    <div className="space-y-2.5 select-none text-xs">
      {/* 1. AlefTrade Wave Engine & Pattern Status Card */}
      <div className="glass-panel p-3 border border-white/10 rounded-2xl space-y-2.5 bg-[#0d1322]/90 shadow-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-2">
          <div className="flex items-center gap-1.5">
            <Boxes size={15} className="text-cyan-400" />
            <h3 className="font-bold text-white text-xs">موتور امواج الیوت (AlefTrade)</h3>
          </div>
          <button
            type="button"
            onClick={onOpenSettings}
            className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-white/5 hover:bg-white/10 text-cyan-400 text-[10px] transition-colors"
            title="تنظیمات پارامترهای رانینگ فلت"
          >
            <Sliders size={11} />
            <span>تنظیمات</span>
          </button>
        </div>

        {activePattern ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5">
              <div className="flex items-center gap-1.5">
                {activePattern.direction === 'bullish' ? (
                  <ArrowUpRight size={14} className="text-emerald-400" />
                ) : (
                  <ArrowDownRight size={14} className="text-rose-400" />
                )}
                <span className="font-bold text-white text-[11px]">{activePattern.name}</span>
              </div>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                  activePattern.direction === 'bullish'
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                }`}
              >
                {activePattern.direction === 'bullish' ? 'صعودی ↗' : 'نزولی ↘'}
              </span>
            </div>

            {/* 5-Point Wave Anatomy (0, 1, A, B, C) */}
            {activePattern.points && activePattern.points.length >= 4 && (
              <div className="space-y-1">
                <span className="text-[10px] text-slate-400">ساختار هندسی ۵ نقطه موج:</span>
                <div className="grid grid-cols-5 gap-1 text-center font-mono text-[10px]">
                  {activePattern.points.map((pt: any) => (
                    <div
                      key={pt.label}
                      className="p-1 rounded-lg bg-black/40 border border-white/5 flex flex-col items-center"
                    >
                      <span
                        className={`font-black ${
                          pt.label === 'C'
                            ? activePattern.direction === 'bullish' ? 'text-emerald-400' : 'text-rose-400'
                            : pt.label === 'A' || pt.label === 'B'
                            ? 'text-amber-400'
                            : 'text-cyan-400'
                        }`}
                      >
                        {pt.label}
                      </span>
                      <span className="text-[9px] text-slate-300 truncate w-full">{formatPrice(pt.price)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Rules Evaluation (Retr B, Retr C, Slope Ratio, Kaufman ER) */}
            {activePattern.rules_evaluation && activePattern.rules_evaluation.length > 0 && (
              <div className="space-y-1 pt-1 border-t border-white/5">
                <span className="text-[10px] text-slate-400">اعتبارسنجی قوانین ریاضی AlefTrade:</span>
                <div className="space-y-1">
                  {activePattern.rules_evaluation.map((r: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between px-2 py-1 rounded bg-slate-950/50 border border-white/5 text-[10px]"
                    >
                      <div className="flex items-center gap-1">
                        <CheckCircle2 size={11} className="text-emerald-400 shrink-0" />
                        <span className="text-slate-300">{r.rule}</span>
                      </div>
                      <span className="font-mono text-cyan-300 font-bold">{r.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Progressive Wave Tracker & Dual Probabilities */}
            <WaveProgressTracker
              patternProbability={patternProbability}
              tradeWinProbability={tradeWinProbability}
              stages={progressiveStages}
              isDeveloping={isDeveloping}
              stageLabel={stageLabel}
            />
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-slate-950/50 border border-white/5 text-center space-y-1.5">
            <Clock size={20} className="text-slate-500 mx-auto animate-pulse" />
            <p className="text-slate-300 font-bold text-[11px]">در حال پایش زنده ساختار امواج</p>
            <p className="text-[10px] text-slate-500">
              چارت در وضعیت خام است و به محض حرکت امواج رانینگ فلت، تحلیل لایو رسم می‌شود.
            </p>
          </div>
        )}
      </div>

      {/* 2. AlefTrade Trade Plan & Risk Management Card */}
      <div className="glass-panel p-3 border border-white/10 rounded-2xl space-y-2 bg-[#0d1322]/90 shadow-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
          <div className="flex items-center gap-1.5">
            <Shield size={14} className="text-cyan-400" />
            <h3 className="font-bold text-white text-xs">ستاپ و مدیریت ریسک AlefTrade</h3>
          </div>
          <div
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
              isWait
                ? 'bg-slate-800 text-slate-400 border border-white/10'
                : isBuy
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
            }`}
          >
            {isWait ? (
              <span>در انتظار الگو (WAIT)</span>
            ) : isBuy ? (
              <>
                <TrendingUp size={11} />
                <span>خرید (LONG)</span>
              </>
            ) : (
              <>
                <TrendingDown size={11} />
                <span>فروش (SHORT)</span>
              </>
            )}
          </div>
        </div>

        {!isWait && analysis.trade_setup?.entry_price ? (
          <div className="space-y-1.5">
            {analysis.trade_setup?.is_live_entry && (
              <div className="flex items-center justify-between px-2 py-1 rounded bg-amber-500/15 border border-amber-500/30 text-[10px] text-amber-300 font-bold">
                <span>ورود لایو درون PRZ (بدون تاخیر)</span>
                <span className="font-mono bg-black/40 px-1 rounded text-white animate-pulse">⚡ LIVE</span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-1.5 text-center font-mono">
              <div className="p-2 rounded-xl bg-slate-950/70 border border-white/5">
                <span className="text-[9.5px] text-slate-400">قیمت ورود:</span>
                <p className="text-xs font-bold text-cyan-300 mt-0.5">{formatPrice(analysis.trade_setup?.entry_price)}</p>
              </div>
              <div className="p-2 rounded-xl bg-slate-950/70 border border-white/5">
                <span className="text-[9.5px] text-slate-400">حد ضرر (SL):</span>
                <p className="text-xs font-bold text-rose-400 mt-0.5">{formatPrice(analysis.trade_setup?.stop_loss)}</p>
              </div>
              <div className="p-2 rounded-xl bg-slate-950/70 border border-white/5">
                <span className="text-[9.5px] text-slate-400">تارگت ۱ [موج B]:</span>
                <p className="text-xs font-bold text-emerald-400 mt-0.5">{formatPrice(analysis.trade_setup?.take_profit_1)}</p>
              </div>
              <div className="p-2 rounded-xl bg-slate-950/70 border border-white/5">
                <span className="text-[9.5px] text-slate-400">تارگت ۲ [اکستنشن]:</span>
                <p className="text-xs font-bold text-purple-400 mt-0.5">{formatPrice(analysis.trade_setup?.take_profit_2)}</p>
              </div>
              <div className="col-span-2 p-1.5 rounded-lg bg-cyan-950/30 border border-cyan-500/20 flex items-center justify-between px-3">
                <span className="text-[10px] text-cyan-300 font-sans">نسبت ریسک به ریوارد (R:R):</span>
                <span className="font-mono font-black text-cyan-300">{analysis.trade_setup?.risk_reward_ratio}x</span>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-[10px] text-slate-500 text-center py-2">
            هیچ سیگنال معاملاتی فعال نیست. پس از ورود قیمت به PRZ، سطوح ورود، SL و TP به صورت زنده فعال می‌شوند.
          </p>
        )}
      </div>

      {/* 3. Detected AlefTrade Patterns List */}
      {detectedPatterns.length > 0 && (
        <div className="glass-panel p-3 border border-white/10 rounded-2xl space-y-2 bg-[#0d1322]/90 shadow-xl">
          <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
            <div className="flex items-center gap-1.5">
              <Search size={13} className="text-emerald-400" />
              <h3 className="font-bold text-white text-xs">الگوهای کشف‌شده AlefTrade ({detectedPatterns.length})</h3>
            </div>
          </div>

          <div className="space-y-1.5 max-h-48 overflow-y-auto custom-scrollbar pr-0.5">
            {displayPatterns.map((pat) => {
              const isSelected = selectedPatternId === pat.id;
              const isDeveloping = (pat as any).is_developing;

              return (
                <div
                  key={pat.id}
                  className={`w-full p-2 rounded-xl border transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'bg-cyan-950/40 border-cyan-500/50 shadow-[0_0_12px_rgba(6,182,212,0.15)]'
                      : 'bg-slate-950/60 border-white/5 hover:border-cyan-500/30 hover:bg-cyan-500/5'
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onFocusPattern?.(pat.time, pat)}
                    className="flex flex-col gap-0.5 text-right flex-1 cursor-pointer"
                  >
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span
                        className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                          isDeveloping
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                            : 'bg-purple-500/20 text-purple-300 border-purple-500/30'
                        }`}
                      >
                        {isDeveloping ? 'PRZ' : 'Running Flat'}
                      </span>
                      {pat.direction === 'bullish' ? (
                        <ArrowUpRight size={12} className="text-emerald-400 shrink-0" />
                      ) : (
                        <ArrowDownRight size={12} className="text-rose-400 shrink-0" />
                      )}
                      <span
                        className={`font-bold text-[11px] truncate ${
                          isSelected ? 'text-cyan-300' : 'text-white group-hover:text-cyan-300'
                        }`}
                      >
                        {pat.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[9px] text-slate-400 font-mono mt-0.5">
                      <span>{formatDualDateTime(pat.time)}</span>
                      {pat.points && pat.points.length > 0 && (
                        <span className="text-cyan-300 font-bold bg-cyan-950/40 px-1 rounded">
                          {pat.points.length}P
                        </span>
                      )}
                    </div>
                  </button>

                  <div className="flex items-center gap-2 shrink-0 pr-2">
                    <button
                      type="button"
                      onClick={() => onInspectPattern?.(pat)}
                      className="p-1 rounded-lg bg-white/5 hover:bg-white/15 text-slate-400 hover:text-cyan-300 transition-colors"
                      title="مشاهده جزئیات کامل و قواعد ریاضی الگو"
                    >
                      <Eye size={13} />
                    </button>
                    <div className="flex flex-col items-end font-mono">
                      <span className="text-[11px] font-bold text-white">{formatPrice(pat.price)}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
