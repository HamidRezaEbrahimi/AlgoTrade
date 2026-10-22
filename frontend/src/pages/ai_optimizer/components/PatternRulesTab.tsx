import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Save, Loader2, Columns, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { PatternRuleColumn, PatternConfig, Rule, Ratio, Threshold } from './PatternRuleColumn';

interface PatternFamily {
  familyId: string;
  name_fa: string;
  name_en: string;
  category: string;
  bullishId: string;
  bearishId: string;
}

const PATTERN_FAMILIES: PatternFamily[] = [
  {
    familyId: 'running_flat',
    name_fa: 'الگوی فلت دونده (Running Flat)',
    name_en: 'Elliott Running Flat',
    category: 'running_flat',
    bullishId: 'running_flat_bullish',
    bearishId: 'running_flat_bearish',
  },
  {
    familyId: 'regular_flat',
    name_fa: 'الگوی فلت عادی (Regular Flat)',
    name_en: 'Elliott Regular Flat',
    category: 'regular_flat',
    bullishId: 'regular_flat_bullish',
    bearishId: 'regular_flat_bearish',
  },
  {
    familyId: 'expanded_flat',
    name_fa: 'الگوی فلت منبسط (Expanded Flat)',
    name_en: 'Elliott Expanded Flat',
    category: 'expanded_flat',
    bullishId: 'expanded_flat_bullish',
    bearishId: 'expanded_flat_bearish',
  },
  {
    familyId: 'zigzag',
    name_fa: 'موتور چندمقیاسی زیگزاگ',
    name_en: 'Adaptive ZigZag Multi-Scale',
    category: 'zigzag',
    bullishId: 'zigzag_bullish',
    bearishId: 'zigzag_bearish',
  },
  {
    familyId: 'risk_manager',
    name_fa: 'مدیریت ریسک و پوزیشن (RMS)',
    name_en: 'Risk & Execution Manager',
    category: 'risk_manager',
    bullishId: 'risk_manager_bullish',
    bearishId: 'risk_manager_bearish',
  },
];

type ViewMode = 'dual' | 'bullish' | 'bearish';

export const PatternRulesTab: React.FC = () => {
  const [patterns, setPatterns] = useState<PatternConfig[]>([]);
  const [selectedFamilyId, setSelectedFamilyId] = useState<string>('running_flat');
  const [viewMode, setViewMode] = useState<ViewMode>('dual');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const loadConfig = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await axios.get('/api/config/pattern-rules');
      if (res.data?.patterns) {
        setPatterns(res.data.patterns);
      }
    } catch (err) {
      console.error('Failed to load pattern rules', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const saveConfig = async () => {
    setIsSaving(true);
    try {
      await axios.post('/api/config/pattern-rules', { patterns });
    } catch (err) {
      console.error('Failed to save', err);
      alert('خطا در ذخیره تنظیمات!');
    } finally {
      setIsSaving(false);
    }
  };

  const currentFamily = useMemo(() => {
    return PATTERN_FAMILIES.find((f) => f.familyId === selectedFamilyId) || PATTERN_FAMILIES[0];
  }, [selectedFamilyId]);

  const bullishPattern = useMemo(() => {
    return patterns.find((p) => p.id === currentFamily.bullishId);
  }, [patterns, currentFamily]);

  const bearishPattern = useMemo(() => {
    return patterns.find((p) => p.id === currentFamily.bearishId);
  }, [patterns, currentFamily]);

  const updateRule = (patId: string, idx: number, field: keyof Rule, val: string) => {
    setPatterns((prev) =>
      prev.map((p) => {
        if (p.id !== patId) return p;
        const rules = [...p.rules];
        rules[idx] = { ...rules[idx], [field]: val };

        if (field === 'var_left' || field === 'operator' || field === 'var_right') {
          const r = rules[idx];
          if (r.operator === 'between') {
            const parts = r.var_right.split(',');
            rules[idx].condition = `${r.var_left} >= ${parts[0]?.trim() || '0'} && ${r.var_left} <= ${parts[1]?.trim() || '1'}`;
          } else {
            rules[idx].condition = `${r.var_left} ${r.operator} ${r.var_right}`;
          }
        }
        return { ...p, rules };
      })
    );
  };

  const updateRatio = (patId: string, ratioKey: string, field: keyof Ratio, val: number) => {
    setPatterns((prev) =>
      prev.map((p) => {
        if (p.id !== patId) return p;
        if (!p.ratios) return p;
        const ratios = p.ratios.map(r => r.key === ratioKey ? { ...r, [field]: val } : r);
        return { ...p, ratios };
      })
    );
  };

  const updateThreshold = (patId: string, thresholdKey: string, field: keyof Threshold, val: number) => {
    setPatterns((prev) =>
      prev.map((p) => {
        if (p.id !== patId) return p;
        if (!p.thresholds) return p;
        const thresholds = p.thresholds.map(t => t.key === thresholdKey ? { ...t, [field]: val } : t);
        return { ...p, thresholds };
      })
    );
  };

  const addRule = (patId: string, group: string) => {
    setPatterns((prev) =>
      prev.map((p) => {
        if (p.id !== patId) return p;
        return {
          ...p,
          rules: [
            ...p.rules,
            {
              rule_id: `new_${Date.now()}`,
              group,
              description: '',
              condition: 'features.metrics.time_ratio <= 1.0',
              var_left: 'features.metrics.time_ratio',
              operator: '<=',
              var_right: '1.0',
            },
          ],
        };
      })
    );
  };

  const removeRule = (patId: string, idx: number) => {
    setPatterns((prev) =>
      prev.map((p) => {
        if (p.id !== patId) return p;
        const rules = [...p.rules];
        rules.splice(idx, 1);
        return { ...p, rules };
      })
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-80 text-slate-500">
        <Loader2 size={24} className="animate-spin" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4" dir="rtl">
      {/* ── Pattern Families List Column ──────────────── */}
      <div className="lg:col-span-1 bg-slate-900/90 border border-white/10 rounded-2xl p-3.5 flex flex-col justify-between space-y-4">
        <div>
          <div className="text-xs font-bold text-slate-300 px-2 py-1 mb-2 flex items-center justify-between">
            <span>الگوهای پایه ({PATTERN_FAMILIES.length})</span>
            <span className="text-[10px] text-cyan-400 font-mono">فیس‌تو‌فیس</span>
          </div>

          <div className="space-y-2">
            {PATTERN_FAMILIES.map((fam) => {
              const isSelected = selectedFamilyId === fam.familyId;
              const bP = patterns.find((p) => p.id === fam.bullishId);
              const beP = patterns.find((p) => p.id === fam.bearishId);
              const totalRules = (bP?.rules.length || 0) + (beP?.rules.length || 0);

              return (
                <button
                  key={fam.familyId}
                  type="button"
                  onClick={() => {
                    setSelectedFamilyId(fam.familyId);
                  }}
                  className={`w-full flex flex-col items-start p-3 rounded-xl transition-all text-right ${
                    isSelected
                      ? 'bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 shadow-md shadow-cyan-500/10'
                      : 'hover:bg-white/5 border border-transparent text-slate-400'
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="font-bold text-xs">{fam.name_fa}</span>
                    <span className="text-[9px] font-mono text-slate-500 uppercase">{fam.category}</span>
                  </div>

                  <div className="flex items-center gap-2 mt-2 w-full justify-between">
                    <div className="flex items-center gap-1.5 text-[9px] font-mono">
                      <span className="text-emerald-400">🟢 {bP?.rules.length || 0}</span>
                      <span className="text-slate-600">|</span>
                      <span className="text-rose-400">🔴 {beP?.rules.length || 0}</span>
                    </div>
                    <span className="text-[9px] px-2 py-0.5 rounded-full bg-white/5 text-slate-400 font-mono">
                      {totalRules} شرط کل
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Save button */}
        <button
          type="button"
          onClick={saveConfig}
          disabled={isSaving}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
        >
          {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
          {isSaving ? 'در حال ذخیره...' : 'ذخیره کل قواعد در سرور'}
        </button>
      </div>

      {/* ── Main Face-to-Face Editor Area ─────────────── */}
      <div className="lg:col-span-3 space-y-4">
        {/* Family Header + View Mode Toggle */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 border border-white/10 p-4 rounded-2xl">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-white">{currentFamily.name_fa}</h2>
              <span className="text-xs text-slate-400 font-mono">({currentFamily.name_en})</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              مقایسه همزمان و ویرایش فیس‌تو‌فیس شروط ساختاری حالت‌های صعودی و نزولی
            </p>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-white/10 text-xs">
            <button
              type="button"
              onClick={() => setViewMode('dual')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all ${
                viewMode === 'dual'
                  ? 'bg-slate-700 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Columns size={13} />
              <span>فیس‌تو‌فیس</span>
            </button>

            <button
              type="button"
              onClick={() => setViewMode('bullish')}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg font-bold transition-all ${
                viewMode === 'bullish'
                  ? 'bg-emerald-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-emerald-400'
              }`}
            >
              <ArrowUpRight size={13} />
              <span>صعودی</span>
            </button>

            <button
              type="button"
              onClick={() => setViewMode('bearish')}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg font-bold transition-all ${
                viewMode === 'bearish'
                  ? 'bg-rose-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-rose-400'
              }`}
            >
              <ArrowDownRight size={13} />
              <span>نزولی</span>
            </button>
          </div>
        </div>

        {/* Columns Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(viewMode === 'dual' || viewMode === 'bullish') && bullishPattern && (
              <div className={viewMode === 'bullish' ? 'col-span-2' : ''}>
                <PatternRuleColumn
                  pattern={bullishPattern}
                  onUpdateRule={updateRule}
                  onAddRule={addRule}
                  onRemoveRule={removeRule}
                  onUpdateRatio={updateRatio}
                  onUpdateThreshold={updateThreshold}
                />
              </div>
            )}

            {(viewMode === 'dual' || viewMode === 'bearish') && bearishPattern && (
              <div className={viewMode === 'bearish' ? 'col-span-2' : ''}>
                <PatternRuleColumn
                  pattern={bearishPattern}
                  onUpdateRule={updateRule}
                  onAddRule={addRule}
                  onRemoveRule={removeRule}
                  onUpdateRatio={updateRatio}
                  onUpdateThreshold={updateThreshold}
                />
              </div>
            )}
          </div>
      </div>
    </div>
  );
};
