import React from 'react';
import { Plus, Trash2, ChevronDown, ChevronRight, Zap, TrendingDown, Shield, Target, Info } from 'lucide-react';

export interface Rule {
  rule_id: string;
  group: string;
  description: string;
  condition: string;
  var_left: string;
  operator: string;
  var_right: string;
}

export interface Ratio {
  key: string;
  title_fa: string;
  title_en: string;
  min: number;
  max: number;
  typical: number;
}

export interface Threshold {
  key: string;
  title_fa: string;
  title_en: string;
  min: number;
  typical: number;
  levels?: {
    weak: number;
    normal: number;
    strong: number;
  };
}

export interface PatternConfig {
  id: string;
  name_en: string;
  name_fa: string;
  category: string;
  direction: string;
  rules: Rule[];
  ratios?: Ratio[];
  thresholds?: Threshold[];
}

export const VARIABLE_CATALOG = [
  {
    group: 'ویژگی‌های هندسی',
    items: [
      { value: 'features.metrics.disp', label: 'اندازه ایمپالس' },
      { value: 'features.metrics.retrace_total', label: 'درصد کل اصلاح' },
      { value: 'features.metrics.atr', label: 'ATR(14)' },
      { value: 'features.metrics.time_ratio', label: 'نسبت زمانی (Time Ratio)' },
      { value: 'features.metrics.range_ratio', label: 'نسبت دامنه (Range Ratio)' },
      { value: 'features.metrics.risk_reward', label: 'ریسک به ریوارد (R/R)' },
    ],
  },
  {
    group: 'نسبت‌های ساختاری',
    items: [
      { value: 'features.ratios.a_retrace', label: 'نسبت موج A به ایمپالس' },
      { value: 'features.ratios.b_over_a', label: 'نسبت موج B به A' },
      { value: 'features.ratios.c_over_a', label: 'نسبت موج C به A' },
      { value: 'features.metrics.b_duration_ratio', label: 'نسبت زمانی موج B' },
      { value: 'features.metrics.c_duration_ratio', label: 'نسبت زمانی موج C' },
    ],
  },
  {
    group: 'تاییدات منطقی (True/False)',
    items: [
      { value: 'features.structure.clean_impulse', label: 'ایمپالس تمیز' },
      { value: 'features.structure.has_internal_structure', label: 'دارای زیرساختار داخلی' },
      { value: 'features.completion.i2_crossed_P4', label: 'عبور موج دوم از P4' },
      { value: 'features.structure.B_breaks_i1_end', label: 'موج B ایمپالس را می‌شکند' },
      { value: 'features.structure.C_breaks_A_end', label: 'موج C از A عبور می‌کند' },
      { value: 'features.structure.i2_opposes_C', label: 'موج دوم خلاف جهت C است' },
    ],
  },
];

export const OPERATORS = [
  { value: '>=', label: '≥ بزرگتر‌مساوی' },
  { value: '<=', label: '≤ کوچکتر‌مساوی' },
  { value: '>', label: '> بزرگتر' },
  { value: '<', label: '< کوچکتر' },
  { value: '==', label: '= مساوی' },
  { value: '!=', label: '≠ نامساوی' },
  { value: 'between', label: '↔ بین (between)' },
];

const GROUP_META: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  impulse: { label: 'ایمپالس اولیه', icon: Zap, color: 'text-amber-400' },
  correction: { label: 'ساختار اصلاح (A-B-C)', icon: TrendingDown, color: 'text-blue-400' },
  structure: { label: 'حفظ سطوح کلیدی', icon: Shield, color: 'text-emerald-400' },
  trade: { label: 'معامله و مدیریت ریسک', icon: Target, color: 'text-rose-400' },
};

interface Props {
  pattern: PatternConfig;
  onUpdateRule: (patId: string, idx: number, field: keyof Rule, val: string) => void;
  onAddRule: (patId: string, group: string) => void;
  onRemoveRule: (patId: string, idx: number) => void;
  onUpdateRatio?: (patId: string, ratioKey: string, field: keyof Ratio, val: number) => void;
  onUpdateThreshold?: (patId: string, thresholdKey: string, field: keyof Threshold, val: number) => void;
}

export const PatternRuleColumn: React.FC<Props> = ({
  pattern,
  onUpdateRule,
  onAddRule,
  onRemoveRule,
  onUpdateRatio,
  onUpdateThreshold,
}) => {
  const [expandedGroups, setExpandedGroups] = React.useState<Record<string, boolean>>({
    impulse: true,
    correction: true,
    structure: true,
    trade: true,
  });

  const toggleGroup = (g: string) => {
    setExpandedGroups((prev) => ({ ...prev, [g]: !prev[g] }));
  };

  const groupedRules = React.useMemo(() => {
    const groups: Record<string, { rule: Rule; originalIdx: number }[]> = {};
    pattern.rules.forEach((r, i) => {
      const g = r.group || 'other';
      if (!groups[g]) groups[g] = [];
      groups[g].push({ rule: r, originalIdx: i });
    });
    return groups;
  }, [pattern.rules]);

  const isBull = pattern.direction === 'bullish';

  return (
    <div className="flex-1 flex flex-col space-y-3 bg-slate-900/60 border border-white/10 rounded-2xl p-3.5">
      {/* Column Header */}
      <div
        className={`flex items-center justify-between p-3 rounded-xl border ${
          isBull
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
        }`}
      >
        <div className="flex items-center gap-2">
          <span className="text-base">{isBull ? '🟢' : '🔴'}</span>
          <div>
            <h3 className="font-bold text-xs">{isBull ? 'حالت صعودی (Bullish)' : 'حالت نزولی (Bearish)'}</h3>
            <span className="text-[10px] font-mono opacity-70">{pattern.id}</span>
          </div>
        </div>
        <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-md bg-white/10">
          {pattern.rules.length} شرط
        </span>
      </div>

      {/* Geometric Parameters (Ratios and Thresholds) */}
      {(pattern.ratios?.length || pattern.thresholds?.length) ? (
        <div className="rounded-xl border border-white/5 overflow-hidden bg-slate-950/60 mb-2.5">
          <button
            type="button"
            onClick={() => toggleGroup('geometric_params')}
            className="w-full flex items-center justify-between px-3.5 py-2.5 bg-slate-900/80 hover:bg-white/[0.03] transition-colors"
          >
            <div className="flex items-center gap-2">
              <Target size={14} className="text-purple-400" />
              <span className="font-bold text-[11px] text-purple-400">پارامترهای هندسی (Ratios & Thresholds)</span>
              <span className="text-[9px] text-slate-500 font-mono">
                ({(pattern.ratios?.length || 0) + (pattern.thresholds?.length || 0)})
              </span>
            </div>
            {expandedGroups['geometric_params'] !== false ? (
              <ChevronDown size={14} className="text-slate-500" />
            ) : (
              <ChevronRight size={14} className="text-slate-500" />
            )}
          </button>
          
          {expandedGroups['geometric_params'] !== false && (
            <div className="p-3 space-y-2.5 bg-[#060a13]">
              {/* Ratios */}
              {pattern.ratios?.map((ratio) => (
                <div key={`ratio-${ratio.key}`} className="p-3 rounded-lg bg-slate-900 border border-white/5 relative flex flex-col gap-2.5">
                  <div className="flex justify-between items-center text-xs font-bold text-slate-200">
                    <span>{ratio.title_fa || ratio.key}</span>
                    <span className="bg-slate-800 text-[10px] px-1.5 py-0.5 rounded text-slate-400 font-mono font-normal">{ratio.key}</span>
                  </div>
                  <div className="flex gap-2 text-xs items-center justify-between" dir="rtl">
                    <div className="flex items-center gap-1.5">
                      <label className="text-slate-400 text-[10px]">حداقل:</label>
                      <input
                        type="number" step="0.01"
                        value={ratio.min}
                        onChange={(e) => onUpdateRatio?.(pattern.id, ratio.key, 'min', parseFloat(e.target.value))}
                        className="bg-slate-950 border border-white/10 rounded w-16 px-1.5 py-1 text-center text-emerald-400 font-mono"
                        dir="ltr"
                      />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <label className="text-slate-400 text-[10px]">معمول:</label>
                      <input
                        type="number" step="0.01"
                        value={ratio.typical}
                        onChange={(e) => onUpdateRatio?.(pattern.id, ratio.key, 'typical', parseFloat(e.target.value))}
                        className="bg-slate-950 border border-white/10 rounded w-16 px-1.5 py-1 text-center text-cyan-400 font-mono"
                        dir="ltr"
                      />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <label className="text-slate-400 text-[10px]">حداکثر:</label>
                      <input
                        type="number" step="0.01"
                        value={ratio.max}
                        onChange={(e) => onUpdateRatio?.(pattern.id, ratio.key, 'max', parseFloat(e.target.value))}
                        className="bg-slate-950 border border-white/10 rounded w-16 px-1.5 py-1 text-center text-rose-400 font-mono"
                        dir="ltr"
                      />
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Thresholds */}
              {pattern.thresholds?.map((threshold) => (
                <div key={`threshold-${threshold.key}`} className="p-3 rounded-lg bg-slate-900 border border-white/5 relative flex flex-col gap-2.5">
                  <div className="flex justify-between items-center text-xs font-bold text-slate-200">
                    <span>{threshold.title_fa || threshold.key}</span>
                    <span className="bg-slate-800 text-[10px] px-1.5 py-0.5 rounded text-slate-400 font-mono font-normal">{threshold.key}</span>
                  </div>
                  <div className="flex gap-2 text-xs items-center justify-start" dir="rtl">
                    <div className="flex items-center gap-1.5">
                      <label className="text-slate-400 text-[10px]">حداقل:</label>
                      <input
                        type="number" step="0.01"
                        value={threshold.min}
                        onChange={(e) => onUpdateThreshold?.(pattern.id, threshold.key, 'min', parseFloat(e.target.value))}
                        className="bg-slate-950 border border-white/10 rounded w-16 px-1.5 py-1 text-center text-emerald-400 font-mono"
                        dir="ltr"
                      />
                    </div>
                    <div className="flex items-center gap-1.5 mr-4">
                      <label className="text-slate-400 text-[10px]">معمول:</label>
                      <input
                        type="number" step="0.01"
                        value={threshold.typical}
                        onChange={(e) => onUpdateThreshold?.(pattern.id, threshold.key, 'typical', parseFloat(e.target.value))}
                        className="bg-slate-950 border border-white/10 rounded w-16 px-1.5 py-1 text-center text-cyan-400 font-mono"
                        dir="ltr"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : null}

      {/* Accordion Groups */}
      <div className="space-y-2.5">
        {Object.entries(groupedRules).map(([groupKey, items]) => {
          const meta = GROUP_META[groupKey] || { label: groupKey, icon: Info, color: 'text-slate-400' };
          const GroupIcon = meta.icon;
          const isExpanded = expandedGroups[groupKey] !== false;

          return (
            <div key={groupKey} className="rounded-xl border border-white/5 overflow-hidden bg-slate-950/60">
              <button
                type="button"
                onClick={() => toggleGroup(groupKey)}
                className="w-full flex items-center justify-between px-3.5 py-2.5 bg-slate-900/80 hover:bg-white/[0.03] transition-colors"
              >
                <div className="flex items-center gap-2">
                  <GroupIcon size={14} className={meta.color} />
                  <span className={`font-bold text-[11px] ${meta.color}`}>{meta.label}</span>
                  <span className="text-[9px] text-slate-500 font-mono">({items.length})</span>
                </div>
                {isExpanded ? (
                  <ChevronDown size={14} className="text-slate-500" />
                ) : (
                  <ChevronRight size={14} className="text-slate-500" />
                )}
              </button>

              {isExpanded && (
                <div className="p-3 space-y-2.5 bg-[#060a13]">
                  {items.map(({ rule, originalIdx }) => (
                    <div
                      key={originalIdx}
                      className="p-3 rounded-lg bg-slate-900 border border-white/5 relative group"
                    >
                      <button
                        type="button"
                        onClick={() => onRemoveRule(pattern.id, originalIdx)}
                        className="absolute top-2.5 left-2.5 p-1 rounded-md text-rose-500/40 hover:bg-rose-500/10 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
                        title="حذف شرط"
                      >
                        <Trash2 size={12} />
                      </button>

                      {/* Description */}
                      <div className="mb-2">
                        <input
                          type="text"
                          value={rule.description}
                          onChange={(e) => onUpdateRule(pattern.id, originalIdx, 'description', e.target.value)}
                          placeholder="توضیح شرط..."
                          className="w-full bg-transparent border-none text-[11px] text-slate-300 focus:outline-none placeholder:text-slate-600"
                        />
                      </div>

                      {/* Visual builder row */}
                      {rule.operator === 'expr_cel' ? (
                        <div className="flex flex-col gap-1 w-full" dir="ltr">
                          <span className="text-[10px] text-slate-400 mb-0.5 text-right font-sans">عبارت منطقی (CEL):</span>
                          <input
                            type="text"
                            value={rule.var_left}
                            onChange={(e) => onUpdateRule(pattern.id, originalIdx, 'var_left', e.target.value)}
                            placeholder="features.metrics.disp > 0.5"
                            className="bg-slate-950 border border-white/10 rounded-lg px-2.5 py-1.5 text-[11px] text-sky-300 font-mono focus:outline-none focus:border-sky-500/50 w-full tracking-wider"
                            dir="ltr"
                          />
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 flex-wrap" dir="ltr">
                          <select
                            value={rule.var_left}
                            onChange={(e) => onUpdateRule(pattern.id, originalIdx, 'var_left', e.target.value)}
                            className="bg-slate-950 border border-white/10 rounded-md px-2 py-1 text-[10px] text-cyan-300 font-mono focus:outline-none focus:border-cyan-500/50 min-w-[110px]"
                          >
                            {VARIABLE_CATALOG.map((grp) => (
                              <optgroup key={grp.group} label={grp.group}>
                                {grp.items.map((v) => (
                                  <option key={v.value} value={v.value}>
                                    {v.value} — {v.label}
                                  </option>
                                ))}
                              </optgroup>
                            ))}
                          </select>

                          <select
                            value={rule.operator}
                            onChange={(e) => onUpdateRule(pattern.id, originalIdx, 'operator', e.target.value)}
                            className="bg-slate-950 border border-amber-500/20 rounded-md px-1.5 py-1 text-[10px] text-amber-300 font-bold focus:outline-none focus:border-amber-500/50 min-w-[65px]"
                          >
                            {OPERATORS.map((op) => (
                              <option key={op.value} value={op.value}>
                                {op.label}
                              </option>
                            ))}
                          </select>

                          <input
                            type="text"
                            value={rule.var_right}
                            onChange={(e) => onUpdateRule(pattern.id, originalIdx, 'var_right', e.target.value)}
                            placeholder={rule.operator === 'between' ? 'min, max' : 'مقدار/متغیر'}
                            className="bg-slate-950 border border-white/10 rounded-md px-2 py-1 text-[10px] text-emerald-300 font-mono focus:outline-none focus:border-emerald-500/50 flex-1 min-w-[90px]"
                          />
                        </div>
                      )}

                      {rule.operator !== 'expr_cel' && (
                        <div className="mt-1.5 text-[10px] text-slate-500 font-mono" dir="ltr">
                          فرمول: <span className="text-cyan-500/70">{rule.condition || '—'}</span>
                        </div>
                      )}
                    </div>
                  ))}

                  <button
                    type="button"
                    onClick={() => onAddRule(pattern.id, groupKey)}
                    className="w-full flex items-center justify-center gap-1 py-1.5 rounded-lg border border-dashed border-white/10 text-slate-500 hover:text-cyan-400 hover:border-cyan-500/30 text-[10px] transition-colors"
                  >
                    <Plus size={12} />
                    افزودن به {meta.label}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
