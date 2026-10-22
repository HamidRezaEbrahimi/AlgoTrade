// frontend/src/pages/trading/components/BarReplayToolbar.tsx
// Glassmorphism control toolbar for TradingView-style Bar Replay.

import React from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Scissors,
  X,
  Gauge,
  Sparkles,
  Zap,
} from 'lucide-react';
import { BarReplayState } from '../hooks/useBarReplay';
import { CandleData } from '../../../stores/useMarketStore';
import { formatDualDateTime } from '../../../utils/dateFormatter';
import { formatPrice } from '../../../components/chart/chartUtils';

interface BarReplayToolbarProps {
  replay: BarReplayState;
  totalCandles: CandleData[];
}

export const BarReplayToolbar: React.FC<BarReplayToolbarProps> = ({
  replay,
  totalCandles,
}) => {
  const {
    isReplayMode,
    isPlaying,
    replayIndex,
    speed,
    isCutting,
    replayAnalysis,
    isAnalyzing,
    togglePlay,
    stepForward,
    stepBackward,
    jumpToIndex,
    setSpeed,
    setIsCutting,
    exitReplay,
  } = replay;

  if (!isReplayMode) return null;

  const currentCandle = totalCandles[replayIndex];
  const currentTime = currentCandle?.time || 0;
  const timeFormatted = formatDualDateTime(currentTime);

  // Status message regarding Elliott waves & Running Flat
  const detectedPatterns = replayAnalysis?.detected_patterns || [];
  const runningFlatPattern = detectedPatterns.find(
    (p) => p.category === 'flat' && (p.name_en?.toLowerCase().includes('running') || p.id.startsWith('running_flat'))
  );
  const developingWavePattern = detectedPatterns.find(
    (p) => p.id.startsWith('dev_') || p.name_en?.toLowerCase().includes('developing')
  );

  const speedOptions = [
    { label: '0.5x', ms: 1000 },
    { label: '1x', ms: 500 },
    { label: '2x', ms: 250 },
    { label: '5x', ms: 100 },
  ];

  return (
    <div className="w-full bg-[#0d1322]/95 border-b border-cyan-500/30 backdrop-blur-md px-3 py-2 flex flex-col gap-2 select-none animate-fade-in shadow-2xl">
      {/* Top Row: Replay Controls & Wave Status Badge */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        {/* Left Controls: Cut, Step Back, Play/Pause, Step Forward, Speed */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Active Replay Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-bold">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span>بازپخش چارت (Replay)</span>
          </div>

          {/* Cut to Bar Tool (Scissors) */}
          <button
            type="button"
            onClick={() => setIsCutting(!isCutting)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-bold transition-all border ${
              isCutting
                ? 'bg-amber-500 text-slate-950 border-amber-400 shadow-md shadow-amber-500/20 animate-pulse'
                : 'bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border-white/10'
            }`}
            title="روی هر کندل در چارت کلیک کنید تا بازپخش از آنجا آغاز شود"
          >
            <Scissors size={13} />
            <span>{isCutting ? 'روی کندل کلیک کنید...' : 'برش نمودار'}</span>
          </button>

          {/* Step Backward (-1) */}
          <button
            type="button"
            onClick={stepBackward}
            disabled={replayIndex <= 30}
            className="p-1.5 rounded-xl bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-white/5 text-slate-300 hover:text-white border border-white/10 transition-colors"
            title="کندل قبلی (-1)"
          >
            <SkipBack size={15} />
          </button>

          {/* Play / Pause Toggle */}
          <button
            type="button"
            onClick={togglePlay}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black transition-all shadow-md ${
              isPlaying
                ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/30'
                : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-cyan-500/30'
            }`}
            title={isPlaying ? 'توقف (Pause)' : 'پخش کندل‌ها (Play)'}
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} fill="currentColor" />}
            <span>{isPlaying ? 'توقف' : 'پخش'}</span>
          </button>

          {/* Step Forward (+1) */}
          <button
            type="button"
            onClick={stepForward}
            disabled={replayIndex >= totalCandles.length - 1}
            className="p-1.5 rounded-xl bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-white/5 text-slate-300 hover:text-white border border-white/10 transition-colors"
            title="کندل بعدی (+1)"
          >
            <SkipForward size={15} />
          </button>

          {/* Speed Presets */}
          <div className="flex items-center bg-black/40 rounded-xl p-0.5 border border-white/10">
            <Gauge size={12} className="text-slate-400 ml-1.5 mr-1" />
            {speedOptions.map((opt) => (
              <button
                key={opt.label}
                type="button"
                onClick={() => setSpeed(opt.ms)}
                className={`px-2 py-0.5 rounded-lg text-[11px] font-mono font-bold transition-all ${
                  speed === opt.ms
                    ? 'bg-cyan-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Right Section: Real-time Wave & Pattern Status + Exit */}
        <div className="flex items-center gap-2">
          {/* Pattern Status Indicator */}
          {runningFlatPattern ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold animate-pulse">
              <Zap size={13} className="text-emerald-400" />
              <span>الگوی رانینگ فلت تایید شد!</span>
              <span className="font-mono text-white text-[11px] bg-black/40 px-1 rounded">
                ورود (P4): {formatPrice(runningFlatPattern.price)}
              </span>
            </div>
          ) : developingWavePattern ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-purple-500/20 border border-purple-500/40 text-purple-300 text-xs font-bold">
              <Sparkles size={13} className="text-purple-400 animate-spin" />
              <span>موج در حال تشکیل درون محدوده PRZ</span>
            </div>
          ) : (
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-xl bg-white/5 border border-white/5 text-slate-400 text-xs">
              <span>{isAnalyzing ? 'در حال تحلیل الگوها...' : 'در حال رصد کندل‌ها'}</span>
            </div>
          )}

          {/* Exit Replay Button */}
          <button
            type="button"
            onClick={exitReplay}
            className="flex items-center gap-1 px-2.5 py-1 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 text-xs font-bold transition-colors"
            title="خروج از حالت بازپخش و بازگشت به نمودار زنده"
          >
            <X size={14} />
            <span className="hidden sm:inline">خروج از بازپخش</span>
          </button>
        </div>
      </div>

      {/* Bottom Row: Scrubber Timeline Slider & Current Timestamp */}
      <div className="flex items-center gap-3 pt-0.5">
        <input
          type="range"
          min={30}
          max={Math.max(30, totalCandles.length - 1)}
          value={replayIndex}
          onChange={(e) => jumpToIndex(parseInt(e.target.value, 10))}
          className="flex-1 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400 focus:outline-none"
        />
        <div className="flex items-center gap-2 text-xs font-mono text-slate-300 whitespace-nowrap">
          <span className="text-cyan-400 font-bold">
            کندل {replayIndex + 1} از {totalCandles.length}
          </span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-300">{timeFormatted}</span>
        </div>
      </div>
    </div>
  );
};
