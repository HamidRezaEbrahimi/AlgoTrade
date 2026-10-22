import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Target,
  Maximize2,
  Minimize2,
  Radio,
  Zap,
  ShieldCheck,
  Search,
  ChevronDown,
  History,
} from 'lucide-react';
import { CriteriaResult } from '../types';

interface Props {
  symbol: string;
  exchange: 'wallex' | 'nobitex' | 'faraz';
  currentPrice: number;
  selectedTf: string;
  onSelectTf: (tf: string) => void;
  onOpenSymbolSearch: () => void;
  analysis: CriteriaResult;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
  onOpenOrderModal?: () => void;
  isWsConnected?: boolean;
  isLoadingMore?: boolean;
  isReplayMode?: boolean;
  onToggleReplay?: () => void;
}

export const ChartSignalHud: React.FC<Props> = ({
  symbol,
  exchange,
  currentPrice,
  selectedTf,
  onSelectTf,
  onOpenSymbolSearch,
  analysis,
  isFullscreen,
  onToggleFullscreen,
  onOpenOrderModal,
  isWsConnected = true,
  isLoadingMore = false,
  isReplayMode = false,
  onToggleReplay,
}) => {
  const timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'];
  const signal = analysis.trade_setup?.signal || 'WAIT';
  const isWait = signal === 'WAIT';
  const isBuy = signal === 'BUY';
  const score = analysis.score ?? 0;
  const isPassed = analysis.passed ?? false;

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
    <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-[#0d1322]/95 backdrop-blur-md border-b border-white/10 select-none">
      {/* Left Section: Integrated Symbol Search Trigger + Timeframe Toolbar + Live Price */}
      <div className="flex flex-wrap items-center gap-2.5">
        {/* Symbol Search Trigger Button */}
        <button
          type="button"
          onClick={onOpenSymbolSearch}
          className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 active:bg-white/15 border border-white/10 rounded-xl transition-all shadow-sm group"
          title="جستجو و تغییر نماد"
        >
          <Search size={14} className="text-cyan-400 group-hover:scale-110 transition-transform" />
          <span className="text-sm font-black font-mono text-white tracking-wide">
            {symbol}
          </span>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
            {exchange}
          </span>
          <ChevronDown size={14} className="text-slate-400 group-hover:text-white transition-colors" />
        </button>

        {/* Integrated Timeframe Selector Toolbar */}
        <div className="flex items-center gap-0.5 bg-black/40 p-0.5 rounded-xl border border-white/10">
          {timeframes.map((tf) => (
            <button
              key={tf}
              type="button"
              onClick={() => onSelectTf(tf)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
                selectedTf.toLowerCase() === tf.toLowerCase()
                  ? 'bg-cyan-500 text-slate-950 shadow-sm shadow-cyan-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Live Price */}
        <div className="flex items-baseline gap-1 px-3 py-1 bg-white/5 rounded-xl border border-white/5">
          <span className="text-[11px] text-slate-400">قیمت:</span>
          <span className="text-sm font-black font-mono text-white">
            {formatPrice(currentPrice)}
          </span>
        </div>

        {/* Loading More Indicator */}
        {isLoadingMore && (
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 animate-pulse">
            <span>دریافت تاریخچه...</span>
          </span>
        )}

        {/* WebSocket Pulse Indicator */}
        <span
          className={`hidden sm:flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
            isWsConnected
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
          }`}
        >
          <Radio size={11} className={isWsConnected ? 'animate-pulse text-emerald-400' : ''} />
          <span>{isWsConnected ? 'لایو وب‌سوکت' : 'در حال اتصال'}</span>
        </span>
      </div>

      {/* Right Section: Score + Signal + SL/TP + Actions */}
      <div className="flex flex-wrap items-center gap-2">
        {/* 8-Criteria Score */}
        <div
          className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-bold border ${
            isPassed
              ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
              : 'bg-amber-500/15 text-amber-400 border-amber-500/30'
          }`}
        >
          <Zap size={13} className={isPassed ? 'text-emerald-400' : 'text-amber-400'} />
          <span>امتیاز:</span>
          <span className="font-mono text-white font-black">{score}/۸</span>
        </div>

        {/* Signal & R:R */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-bold border ${
            isWait
              ? 'bg-slate-850 text-slate-400 border-white/10'
              : isBuy
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm'
              : 'bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-sm'
          }`}
        >
          {isWait ? (
            <span>در انتظار الگوی AlefTrade</span>
          ) : (
            <>
              {isBuy ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
              <span>{isBuy ? 'خرید (LONG)' : 'فروش (SHORT)'}</span>
              {analysis.trade_setup?.is_live_entry && (
                <span className="text-[9px] px-1.5 py-0.2 bg-amber-500/30 text-amber-200 rounded font-black border border-amber-400/40 animate-pulse">
                  PRZ LIVE ⚡
                </span>
              )}
              <span className="text-[10px] font-mono px-1 bg-black/40 rounded text-cyan-300">
                {analysis.trade_setup?.risk_reward_ratio}x
              </span>
            </>
          )}
        </div>

        {/* Dual Probabilities HUD Pill */}
        {((analysis.pattern_probability ?? 0) > 0 || (analysis.trade_win_probability ?? 0) > 0) && (
          <div className="hidden 2xl:flex items-center gap-2 px-2.5 py-1 rounded-xl text-xs font-bold bg-white/5 border border-white/10">
            {Boolean(analysis.pattern_probability) && (
              <span className="text-[10px] text-cyan-300 font-mono">
                P<sub>form</sub>: <b>{analysis.pattern_probability}%</b>
              </span>
            )}
            {Boolean(analysis.trade_win_probability) && (
              <span className="text-[10px] text-emerald-400 font-mono">
                P<sub>win</sub>: <b>{analysis.trade_win_probability}%</b>
              </span>
            )}
          </div>
        )}

        {/* Stop Loss (SL) */}
        {!isWait && analysis.trade_setup?.stop_loss && analysis.trade_setup.stop_loss > 0 && (
          <div className="hidden lg:flex items-center gap-1 px-2 py-1 bg-rose-500/10 border border-rose-500/20 rounded-xl text-[11px] font-bold text-rose-300">
            <ShieldAlert size={12} className="text-rose-400" />
            <span>SL:</span>
            <span className="font-mono text-white">
              {formatPrice(analysis.trade_setup.stop_loss)}
            </span>
          </div>
        )}

        {/* Target 1 (TP1) */}
        {!isWait && analysis.trade_setup?.take_profit_1 && analysis.trade_setup.take_profit_1 > 0 && (
          <div className="hidden xl:flex items-center gap-1 px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-[11px] font-bold text-emerald-300">
            <Target size={12} className="text-emerald-400" />
            <span>TP1:</span>
            <span className="font-mono text-white">
              {formatPrice(analysis.trade_setup.take_profit_1)}
            </span>
          </div>
        )}

        {/* Bar Replay Mode Toggle Button */}
        {onToggleReplay && (
          <button
            type="button"
            onClick={onToggleReplay}
            title={isReplayMode ? 'خروج از بازپخش' : 'شروع بازپخش کندل‌ها (Bar Replay)'}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-bold transition-all border ${
              isReplayMode
                ? 'bg-cyan-500 text-slate-950 border-cyan-400 shadow-md shadow-cyan-500/30 font-black animate-pulse'
                : 'bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border-cyan-500/20'
            }`}
          >
            <History size={14} className={isReplayMode ? 'text-slate-950' : 'text-cyan-400'} />
            <span className="hidden sm:inline">بازپخش</span>
          </button>
        )}

        {/* Safety Order Quick Button */}
        {onOpenOrderModal && (
          <button
            type="button"
            onClick={onOpenOrderModal}
            className="flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-bold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 transition-all shadow-sm"
          >
            <ShieldCheck size={14} />
            <span className="hidden sm:inline">سفارش ایمن</span>
          </button>
        )}

        {/* Fullscreen Toggle Button */}
        <button
          type="button"
          onClick={onToggleFullscreen}
          title={isFullscreen ? 'خروج از تمام‌صفحه' : 'تمام‌صفحه چارت'}
          className="p-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white transition-all shadow-sm"
        >
          {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
        </button>
      </div>
    </div>
  );
};
