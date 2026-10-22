import React, { useState, useEffect } from 'react';
import { Sliders, CheckCircle2, RotateCcw, X, Info, Database } from 'lucide-react';
import { DetectorConfig } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  config: DetectorConfig;
  onSaveConfig: (newConfig: DetectorConfig) => void;
}

export const PatternSettingsModal: React.FC<Props> = ({
  isOpen,
  onClose,
  config,
  onSaveConfig,
}) => {
  const [localConfig, setLocalConfig] = useState<DetectorConfig>({ ...config });
  const [recorderMode, setRecorderMode] = useState<'auto' | 'manual' | 'disabled'>('auto');

  useEffect(() => {
    if (isOpen) {
      fetch('/api/patterns/recorder/config')
        .then((r) => r.json())
        .then((data) => {
          if (data?.mode) setRecorderMode(data.mode);
        })
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleReset = () => {
    const defaults: DetectorConfig = {
      min_impulse_atr: 1.5,
      flag_max_retrace: 0.382,
      flat_max_retrace: 0.70,
      wave_b_min_retrace: 0.25,
      min_risk_reward: 1.5,
    };
    setLocalConfig(defaults);
    setRecorderMode('auto');
  };

  const handleSave = () => {
    onSaveConfig(localConfig);
    fetch('/api/patterns/recorder/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: recorderMode }),
    }).catch(() => {});
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in select-none">
      <div className="relative w-full max-w-xl bg-[#0b101b] border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-300">
              <Sliders size={18} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white font-sans">
                تنظیمات و قواعد تشخیص الگوها (Pattern Fine-Tuning)
              </h2>
              <p className="text-[10px] text-slate-400 font-mono">
                تنظیم آستانه‌ها و شروط ریاضی استخراج امواج پرچم و فلت
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

        {/* Body Form */}
        <div className="p-6 overflow-y-auto custom-scrollbar space-y-5 text-xs">
          {/* 1. Min Impulse ATR Mult */}
          <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-white">حداقل شتاب ایمپالس اولیه (ضریب ATR):</span>
                <span className="text-[10px] text-cyan-400 font-mono font-bold">
                  {localConfig.min_impulse_atr.toFixed(1)}x ATR
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">پیش‌فرض: 1.5x</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="3.0"
              step="0.1"
              value={localConfig.min_impulse_atr}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, min_impulse_atr: parseFloat(e.target.value) })
              }
              className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
            />
            <p className="text-[10px] text-slate-400">
              حرکت P0 تا P1 باید حداقل به این میزان از میانگین نوسان بازار بزرگتر باشد تا یک موج ایمپالس معتبر تلقی شود.
            </p>
          </div>

          {/* 2. Flag Max Retrace % */}
          <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-amber-300">حداکثر درصد اصلاح پرچم (Flag Retrace %):</span>
                <span className="text-[10px] text-amber-400 font-mono font-bold">
                  {(localConfig.flag_max_retrace * 100).toFixed(1)}%
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">پیش‌فرض: 38.2% (فیبوناچی)</span>
            </div>
            <input
              type="range"
              min="0.20"
              max="0.50"
              step="0.01"
              value={localConfig.flag_max_retrace}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, flag_max_retrace: parseFloat(e.target.value) })
              }
              className="w-full accent-amber-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
            />
            <p className="text-[10px] text-slate-400">
              اگر اصلاح کل موج کارکشن (P1 تا P4) کمتر از این مقدار باشد، به عنوان پرچم (Flag) و در غیر این صورت فلت (Flat) طبقه‌بندی می‌شود.
            </p>
          </div>

          {/* 3. Wave B Min Retrace % */}
          <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-purple-300">حداقل اصلاح موج B نسبت به موج A:</span>
                <span className="text-[10px] text-purple-400 font-mono font-bold">
                  {(localConfig.wave_b_min_retrace * 100).toFixed(0)}%
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">پیش‌فرض: 25%</span>
            </div>
            <input
              type="range"
              min="0.15"
              max="0.60"
              step="0.05"
              value={localConfig.wave_b_min_retrace}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, wave_b_min_retrace: parseFloat(e.target.value) })
              }
              className="w-full accent-purple-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
            />
            <p className="text-[10px] text-slate-400">
              موج B باید حداقل به این نسبت از موج A در جهت روند اولیه حرکت کند تا تشکیل اصلاح ۳‌موجی قطعی شود.
            </p>
          </div>

          {/* 4. Min Risk/Reward Ratio */}
          <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-white/5 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-emerald-300">حداقل نسبت سود به ریسک (R/R):</span>
                <span className="text-[10px] text-emerald-400 font-mono font-bold">
                  {localConfig.min_risk_reward.toFixed(1)}:1
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">پیش‌فرض: 1.5</span>
            </div>
            <input
              type="range"
              min="1.2"
              max="3.0"
              step="0.1"
              value={localConfig.min_risk_reward}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, min_risk_reward: parseFloat(e.target.value) })
              }
              className="w-full accent-emerald-400 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
            />
            <p className="text-[10px] text-slate-400">
              محاسبه تارگت‌های اولیه و شرط تایید ستاپ معاملاتی خروجی الگوریتم بر پایه این نسبت اعمال می‌شود.
            </p>
          </div>

          {/* AI Pattern Recording Mode */}
          <div className="space-y-2.5 p-3.5 rounded-2xl bg-slate-900/90 border border-purple-500/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database size={15} className="text-purple-400" />
                <span className="font-bold text-white text-xs">وضعیت ضبط و آموزش هوش مصنوعی (ML Dataset):</span>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded-lg border font-bold ${
                recorderMode === 'auto' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
                recorderMode === 'manual' ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' :
                'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                {recorderMode === 'auto' ? 'خودکار (ACTIVE)' : recorderMode === 'manual' ? 'دستی (MANUAL)' : 'غیرفعال (OFF)'}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <button
                type="button"
                onClick={() => setRecorderMode('auto')}
                className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 transition-all ${
                  recorderMode === 'auto'
                    ? 'bg-purple-600/30 border-purple-500 text-white font-bold shadow-lg shadow-purple-500/20'
                    : 'bg-white/[0.02] border-white/10 text-slate-400 hover:text-white'
                }`}
              >
                <span className="text-sm">⚡ خودکار (Auto)</span>
                <span className="text-[9px] text-slate-400">ذخیره خودکار تمام الگوها</span>
              </button>

              <button
                type="button"
                onClick={() => setRecorderMode('manual')}
                className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 transition-all ${
                  recorderMode === 'manual'
                    ? 'bg-purple-600/30 border-purple-500 text-white font-bold shadow-lg shadow-purple-500/20'
                    : 'bg-white/[0.02] border-white/10 text-slate-400 hover:text-white'
                }`}
              >
                <span className="text-sm">👆 دستی (Manual)</span>
                <span className="text-[9px] text-slate-400">ذخیره با کلیک کاربر</span>
              </button>

              <button
                type="button"
                onClick={() => setRecorderMode('disabled')}
                className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 transition-all ${
                  recorderMode === 'disabled'
                    ? 'bg-rose-950/40 border-rose-500/50 text-rose-300 font-bold'
                    : 'bg-white/[0.02] border-white/10 text-slate-400 hover:text-white'
                }`}
              >
                <span className="text-sm">⏸️ غیرفعال (Off)</span>
                <span className="text-[9px] text-slate-400">بدون ذخیره‌سازی داده</span>
              </button>
            </div>
          </div>

          {/* Rule Reference Info Box */}
          <div className="p-3 rounded-xl bg-cyan-950/20 border border-cyan-500/20 flex gap-2 text-[10px] text-cyan-200">
            <Info size={16} className="text-cyan-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-bold">قواعد طبقه‌بندی ریاضی الگوها:</p>
              <ul className="list-disc list-inside space-y-0.5 text-slate-300 font-mono text-[9.5px]">
                <li><b>Bull/Bear Flag</b>: اصلاح $\le$ { (localConfig.flag_max_retrace * 100).toFixed(0) }% و موج B از P1 عبور نمی‌کند.</li>
                <li><b>Expanded Flat</b>: موج B از P1 عبور کرده و موج C نیز از P2 عبور می‌کند (False Breakout دوطرفه).</li>
                <li><b>Running Flat</b>: موج B از P1 عبور کرده ولی موج C توان شکست P2 را ندارد (قدرت بالای روند).</li>
                <li><b>Contract Flat</b>: موج B کمتر از P1 و موج C کمتر از P2 (مثلث اصلاحی متقارن).</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-white/10 flex items-center justify-between bg-white/[0.02]">
          <button
            type="button"
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 text-xs transition-colors font-medium"
          >
            <RotateCcw size={14} />
            <span>بازنشانی به پیش‌فرض</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 text-xs transition-colors"
            >
              انصراف
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all"
            >
              <CheckCircle2 size={15} />
              <span>ذخیره و اعمال روی چارت</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
