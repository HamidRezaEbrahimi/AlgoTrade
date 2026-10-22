// frontend/src/pages/trading/components/WaveProgressTracker.tsx
// Displays progressive wave formation stages (P0→P1→A→B→PRZ→C)
// and dual probability metrics (Pattern Formation Probability & Trade Win Probability).

import React from 'react';
import {
  Activity,
  Flame,
  Crosshair,
} from 'lucide-react';
import { ProgressiveStage } from '../types';

interface Props {
  patternProbability?: number;
  tradeWinProbability?: number;
  stages?: ProgressiveStage[];
  isDeveloping?: boolean;
  stageLabel?: string;
}

export const WaveProgressTracker: React.FC<Props> = ({
  patternProbability = 0,
  tradeWinProbability = 0,
  stages = [],
  isDeveloping = false,
  stageLabel,
}) => {
  if (patternProbability === 0 && tradeWinProbability === 0 && stages.length === 0) {
    return null;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
      case 'TARGET_HIT':
        return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
      case 'ACTIVE':
        return 'text-amber-400 border-amber-500/30 bg-amber-500/10 animate-pulse';
      case 'READY_TO_TRIGGER':
        return 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10 font-black animate-pulse';
      case 'FAILED':
      case 'INVALIDATED':
        return 'text-rose-400 border-rose-500/30 bg-rose-500/10 font-bold';
      default:
        return 'text-slate-500 border-white/5 bg-slate-900/40';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'تکمیل شد ✓';
      case 'TARGET_HIT':
        return 'تارگت محقق شد 🎯';
      case 'ACTIVE':
        return 'در حال تشکیل...';
      case 'READY_TO_TRIGGER':
        return 'آماده تریگر ⚡';
      case 'FAILED':
      case 'INVALIDATED':
        return 'نقض شد ✕';
      default:
        return 'در انتظار';
    }
  };

  return (
    <div className="space-y-2.5 pt-2 border-t border-white/10 select-none">
      {/* 1. Dual Probability Progress Bars */}
      <div className="space-y-1.5 p-2 rounded-xl bg-slate-950/80 border border-white/5">
        <div className="flex items-center justify-between text-[10px]">
          <div className="flex items-center gap-1 text-slate-300 font-bold">
            <Activity size={12} className="text-cyan-400" />
            <span>احتمال وقوع و تکمیل الگو (P<sub>formation</sub>):</span>
          </div>
          <span className="font-mono font-black text-cyan-300">{patternProbability}%</span>
        </div>
        <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-white/5">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(0, patternProbability))}%` }}
          />
        </div>

        <div className="flex items-center justify-between text-[10px] pt-1">
          <div className="flex items-center gap-1 text-slate-300 font-bold">
            <Flame size={12} className="text-emerald-400" />
            <span>احتمال موفقیت پوزیشن (P<sub>win</sub>):</span>
          </div>
          <span className="font-mono font-black text-emerald-300">{tradeWinProbability}%</span>
        </div>
        <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-white/5">
          <div
            className="h-full bg-gradient-to-r from-teal-500 to-emerald-400 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(0, tradeWinProbability))}%` }}
          />
        </div>

        {stageLabel && (
          <div className="pt-1 flex items-center justify-between text-[9px] text-slate-400">
            <span>وضعیت جاری:</span>
            <span className="font-bold text-amber-300 font-sans">{stageLabel}</span>
          </div>
        )}
      </div>

      {/* 2. Progressive 5-Stage Stepper */}
      {stages.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[10px] text-slate-400">
            <div className="flex items-center gap-1">
              <Crosshair size={12} className="text-amber-400" />
              <span className="font-bold text-white">ردیابی لایو مراحل ۵ گانه موج:</span>
            </div>
            {isDeveloping && (
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono animate-pulse">
                LIVE
              </span>
            )}
          </div>

          <div className="space-y-1">
            {stages.map((st) => (
              <div
                key={st.step}
                className={`p-1.5 rounded-lg border flex items-center justify-between text-[9.5px] transition-all ${
                  st.status === 'READY_TO_TRIGGER'
                    ? 'bg-cyan-950/40 border-cyan-500/40 shadow-sm'
                    : st.status === 'ACTIVE'
                    ? 'bg-amber-950/30 border-amber-500/30'
                    : st.passed
                    ? 'bg-slate-950/60 border-white/5'
                    : 'bg-slate-950/30 border-white/5 opacity-50'
                }`}
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span
                    className={`w-4 h-4 rounded-full flex items-center justify-center font-mono font-bold text-[9px] shrink-0 ${
                      st.passed
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : st.status === 'ACTIVE'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-slate-800 text-slate-500 border border-white/10'
                    }`}
                  >
                    {st.step}
                  </span>
                  <div className="flex flex-col truncate">
                    <span className="font-bold text-slate-200 truncate">{st.name}</span>
                    <span className="text-[8.5px] text-slate-400 font-mono truncate">{st.detail}</span>
                  </div>
                </div>

                <span
                  className={`text-[8.5px] font-bold px-1.5 py-0.5 rounded-full border shrink-0 ${getStatusColor(
                    st.status,
                  )}`}
                >
                  {getStatusText(st.status)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
