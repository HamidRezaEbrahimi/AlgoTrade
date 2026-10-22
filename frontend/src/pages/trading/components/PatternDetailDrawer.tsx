import React, { useState } from 'react';
import { Shield, Zap, TrendingUp, TrendingDown, X, Layers, CheckCircle2, BookmarkPlus } from 'lucide-react';
import { PatternMarker } from '../types';
import { formatDualDateTime } from '../../../utils/dateFormatter';

interface Props {
  pattern: PatternMarker | null;
  onClose: () => void;
}

export const PatternDetailDrawer: React.FC<Props> = ({ pattern, onClose }) => {
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  if (!pattern) return null;

  const isBull = pattern.direction === 'bullish';
  const isFlag = pattern.category === 'flag';
  const isFlat = pattern.category === 'flat';
  const isWedge = pattern.category === 'wedge';

  const handleManualSave = async () => {
    if (!pattern) return;
    setSaveStatus('saving');
    try {
      const res = await fetch('/api/patterns/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pattern,
          symbol: 'ACTIVE_SYMBOL',
          timeframe: '1h',
        }),
      });
      if (res.ok) {
        setSaveStatus('saved');
      } else {
        setSaveStatus('error');
      }
    } catch {
      setSaveStatus('error');
    }
  };

  const formatPrice = (val?: number) => {
    if (val === undefined || val === null || val === 0) return '---';
    if (val >= 1000) return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
    return val.toFixed(2);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in select-none">
      <div className="relative w-full max-w-lg bg-[#0b101b] border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-2xl flex items-center justify-center border text-sm"
              style={{
                backgroundColor: `${pattern.pattern_color || '#a855f7'}20`,
                borderColor: `${pattern.pattern_color || '#a855f7'}40`,
                color: pattern.pattern_color || '#a855f7',
              }}
            >
              {isFlag ? '🚩' : isFlat ? '🟣' : isWedge ? '📐' : '🕯️'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white font-sans">{pattern.name}</h2>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-lg border flex items-center gap-1 ${
                    isBull
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                      : 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                  }`}
                >
                  {isBull ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                  <span>{isBull ? 'صعودی (LONG)' : 'نزولی (SHORT)'}</span>
                </span>
                {pattern.lifecycle_status === 'INVALIDATED' || pattern.is_invalidated ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-lg border bg-rose-500/20 text-rose-300 border-rose-500/30">
                    باطل شده ✕
                  </span>
                ) : pattern.lifecycle_status === 'TARGET_HIT' || pattern.is_target_hit ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-lg border bg-emerald-500/20 text-emerald-300 border-emerald-500/30">
                    تارگت خورده 🎯
                  </span>
                ) : (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-lg border bg-cyan-500/20 text-cyan-300 border-cyan-500/30">
                    فعال ⚡
                  </span>
                )}
              </div>
              <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                شناسه: {pattern.id} | زمان تایید: {formatDualDateTime(pattern.time)}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto custom-scrollbar space-y-5 text-xs">
          {/* Status Alert Banner */}
          {pattern.lifecycle_status === 'INVALIDATED' || pattern.is_invalidated ? (
            <div className="p-3 rounded-2xl bg-slate-900/90 border border-rose-500/40 flex items-start gap-2.5 text-rose-300 shadow-lg">
              <div className="w-6 h-6 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0 mt-0.5 font-bold">
                ✕
              </div>
              <div>
                <div className="font-bold text-xs text-rose-300">الگوی باطل شده (INVALIDATED)</div>
                <div className="text-[10.5px] text-slate-300 font-sans mt-0.5 leading-relaxed">
                  {pattern.invalidation_reason || 'قیمت با عبور از تراز P0 کل ساختار الگو را نقض کرده و ستاپ معامله فاقد اعتبار است.'}
                </div>
              </div>
            </div>
          ) : pattern.lifecycle_status === 'TARGET_HIT' || pattern.is_target_hit ? (
            <div className="p-3 rounded-2xl bg-emerald-950/50 border border-emerald-500/40 flex items-start gap-2.5 text-emerald-300 shadow-lg">
              <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-xs text-emerald-300">الگوی موفق - تارگت محقق شد (TARGET HIT 🎯)</div>
                <div className="text-[10.5px] text-slate-300 font-sans mt-0.5 leading-relaxed">
                  حرکت قیمت پس از تکمیل نقطه C به تارگت اول سود رسید و بدون نقض تراز P0 با سود بسته شد.
                </div>
              </div>
            </div>
          ) : null}

          {/* Pattern Quality Grade (STRONG / NORMAL / WEAK) */}
          {pattern.quality_grade && (
            <div className="p-3 rounded-2xl bg-slate-900/80 border border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className="px-2.5 py-1 rounded-xl text-xs font-bold font-mono border"
                  style={{
                    backgroundColor: `${pattern.grade_color || '#10b981'}20`,
                    borderColor: `${pattern.grade_color || '#10b981'}40`,
                    color: pattern.grade_color || '#10b981',
                  }}
                >
                  {pattern.quality_grade === 'STRONG' ? '⭐ درجه کیفی: قوی (Grade A)' :
                   pattern.quality_grade === 'NORMAL' ? '🔹 درجه کیفی: نرمال (Grade B)' : '⚠️ درجه کیفی: ضعیف (Grade C)'}
                </span>
                <span className="text-[11px] text-slate-300 font-sans">
                  نمره کیفیت: <strong className="font-mono text-white">{pattern.quality_score ?? 85}/100</strong>
                </span>
              </div>
              {pattern.quality_strengths && pattern.quality_strengths.length > 0 && (
                <span className="text-[10px] text-emerald-400 font-sans hidden sm:inline">
                  {pattern.quality_strengths[0]}
                </span>
              )}
            </div>
          )}

          {/* 1. 6-Point Structure Decomposition */}
          {pattern.points && pattern.points.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-slate-300 font-bold">
                  <Layers size={14} className="text-cyan-400" />
                  <span>تفکیک نقاط ۶‌گانه موج ({pattern.points.length}P):</span>
                </div>
                <span className="text-[10px] text-cyan-400 font-mono">
                  اطمینان ساختار: {(pattern.confidence * 100).toFixed(0)}%
                </span>
              </div>

              <div className="grid grid-cols-1 gap-1.5 font-mono">
                {pattern.points.map((pt, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2 rounded-xl bg-slate-950/60 border border-white/5 text-[11px]"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="w-5 h-5 rounded-lg flex items-center justify-center text-[10px] font-bold"
                        style={{
                          backgroundColor: `${pattern.pattern_color || '#a855f7'}20`,
                          color: pattern.pattern_color || '#a855f7',
                        }}
                      >
                        P{idx}
                      </span>
                      <span className="text-slate-300 font-sans text-xs">{pt.label}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-slate-500">{formatDualDateTime(pt.time)}</span>
                      <span className="font-bold text-white text-xs">{formatPrice(pt.price)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 2. Trade Zones (Per-Pattern Entry A/B, SL, TP1, TP2) */}
          {pattern.trade_zones && (
            <div className="space-y-2 pt-2 border-t border-white/5">
              <div className="flex items-center gap-1.5 text-slate-300 font-bold">
                <Shield size={14} className="text-emerald-400" />
                <span>نواحی معاملاتی اختصاصی الگو:</span>
              </div>

              <div className="grid grid-cols-1 gap-1.5 font-mono">
                {/* Entry A, B & Stop Loss */}
                {[
                  { tag: 'A', z: pattern.trade_zones.entry_a, c: 'text-cyan-300 bg-cyan-500/20 border-cyan-500/20' },
                  { tag: 'B', z: pattern.trade_zones.entry_b, c: 'text-blue-300 bg-blue-500/20 border-blue-500/20' },
                  { tag: 'SL', z: pattern.trade_zones.stop_loss, c: 'text-rose-400 bg-rose-500/20 border-rose-500/20' },
                ].map(({ tag, z, c }) => (
                  <div key={tag} className={`p-2.5 rounded-xl bg-slate-950/70 border flex items-center justify-between ${c.split(' ')[2]}`}>
                    <div className="flex items-center gap-2">
                      <span className={`w-5 h-5 rounded-lg flex items-center justify-center text-[10px] font-bold ${c.split(' ').slice(0, 2).join(' ')}`}>{tag}</span>
                      <span className="text-slate-300 font-sans text-xs">{z.label}</span>
                    </div>
                    <span className={`text-xs font-bold ${c.split(' ')[0]}`}>{formatPrice(z.price)}</span>
                  </div>
                ))}
                {/* TP1 & TP2 */}
                <div className="grid grid-cols-2 gap-1.5">
                  <div className="p-2.5 rounded-xl bg-slate-950/70 border border-emerald-500/20 text-center">
                    <span className="text-[10px] text-slate-400">تارگت ۱ (TP1)</span>
                    <p className="text-xs font-bold text-emerald-400 mt-0.5">{formatPrice(pattern.trade_zones.tp1.price)}</p>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950/70 border border-purple-500/20 text-center">
                    <span className="text-[10px] text-slate-400">تارگت ۲ (TP2)</span>
                    <p className="text-xs font-bold text-purple-400 mt-0.5">{formatPrice(pattern.trade_zones.tp2.price)}</p>
                  </div>
                </div>

                {/* RR Ratio */}
                {pattern.trade_setup && (
                  <div className="p-2 rounded-xl bg-white/[0.03] border border-white/5 text-center">
                    <span className="text-[10px] text-slate-400">نسبت ریسک به ریوارد (R:R):</span>
                    <span className={`text-xs font-bold mr-2 ${
                      pattern.trade_setup.risk_reward_ratio >= 1.5 ? 'text-emerald-400' :
                      pattern.trade_setup.risk_reward_ratio >= 1.0 ? 'text-amber-400' : 'text-rose-400'
                    }`}>
                      1:{pattern.trade_setup.risk_reward_ratio.toFixed(1)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Fallback: Legacy trade_setup if no trade_zones */}
          {!pattern.trade_zones && pattern.trade_setup && (
            <div className="space-y-2 pt-2 border-t border-white/5">
              <div className="flex items-center gap-1.5 text-slate-300 font-bold"><Shield size={14} className="text-emerald-400" /><span>ستاپ معاملاتی:</span></div>
              <div className="grid grid-cols-2 gap-2 text-center font-mono">
                {[
                  { label: 'ورود:', val: pattern.trade_setup.entry, c: 'text-cyan-300 border-cyan-500/20' },
                  { label: 'حد ضرر:', val: pattern.trade_setup.stop_loss, c: 'text-rose-400 border-rose-500/20' },
                  { label: 'تارگت ۱:', val: pattern.trade_setup.take_profit_1, c: 'text-emerald-400 border-emerald-500/20' },
                  { label: 'تارگت ۲:', val: pattern.trade_setup.take_profit_2, c: 'text-purple-400 border-purple-500/20' },
                ].map((s, i) => (
                  <div key={i} className={`p-2.5 rounded-xl bg-slate-950/70 border ${s.c.split(' ')[1]}`}>
                    <span className="text-[10px] text-slate-400">{s.label}</span>
                    <p className={`text-xs font-bold mt-0.5 ${s.c.split(' ')[0]}`}>{formatPrice(s.val)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Context Tags (CHoCH, Volume, RSI, Trend) */}
          {pattern.context_tags && pattern.context_tags.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-white/5">
              <div className="flex items-center gap-1.5 text-slate-300 font-bold">
                <Zap size={14} className="text-violet-400" />
                <span>تاییدیه‌های زمینه‌ای (Context Filters):</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {pattern.context_tags.map((tag, i) => (
                  <div key={i} className={`px-2.5 py-1.5 rounded-xl border text-[11px] font-mono flex items-center gap-1.5 ${
                    tag.passed ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                  }`}>
                    <span>{tag.passed ? '✅' : '⚠️'}</span>
                    <span className="font-sans">{tag.label}</span>
                    <span className="text-[9px] text-slate-500">{tag.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 4. Rules Evaluation Checklist */}
          {pattern.rules_evaluation && pattern.rules_evaluation.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-white/5">
              <div className="flex items-center gap-1.5 text-slate-300 font-bold">
                <CheckCircle2 size={14} className="text-amber-400" />
                <span>قواعد هندسی (YAML Rules):</span>
              </div>

              <div className="space-y-1 font-mono">
                {pattern.rules_evaluation.map((r, i) => (
                  <div
                    key={i}
                    className="p-2 rounded-xl bg-slate-950/40 border border-emerald-500/20 flex items-center justify-between text-[11px]"
                  >
                    <div className="flex items-center gap-2">
                      <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
                      <span className="text-slate-300 font-sans text-xs">{r.rule}</span>
                      <span className="text-[9.5px] text-slate-500">({r.condition})</span>
                    </div>
                    <span className="text-emerald-400 font-bold text-xs">{r.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-white/10 flex items-center justify-between bg-white/[0.02]">
          <button
            type="button"
            onClick={handleManualSave}
            disabled={saveStatus === 'saving' || saveStatus === 'saved'}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              saveStatus === 'saved'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : saveStatus === 'saving'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 animate-pulse'
                : 'bg-purple-600/30 hover:bg-purple-600/50 text-purple-200 border border-purple-500/30'
            }`}
          >
            <BookmarkPlus size={14} />
            <span>{saveStatus === 'saved' ? '✓ در دیتاست ثبت شد' : saveStatus === 'saving' ? 'در حال ثبت...' : 'ذخیره در بانک الگوها'}</span>
          </button>
          <button type="button" onClick={onClose} className="px-5 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white font-medium text-xs transition-colors">
            بستن پنجره
          </button>
        </div>
      </div>
    </div>
  );
};
