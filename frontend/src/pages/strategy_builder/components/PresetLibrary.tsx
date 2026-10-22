import React from 'react';
import { useTranslation } from 'react-i18next';
import { BookmarkCheck, Sparkles } from 'lucide-react';
import { PresetTemplate } from '../types';
import { InfoTooltip } from './InfoTooltip';

interface Props {
  presets: PresetTemplate[];
  onApplyPreset: (preset: PresetTemplate) => void;
  selectedPresetId?: string;
}

export const PresetLibrary: React.FC<Props> = ({ presets, onApplyPreset, selectedPresetId }) => {
  const { t } = useTranslation('StrategyBuilder');

  return (
    <div className="glass-panel p-3.5 space-y-2.5 border border-white/10 rounded-2xl h-full flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <div className="flex items-center gap-1.5">
          <BookmarkCheck size={15} className="text-cyan-400" />
          <h3 className="text-xs font-bold text-white">{t('presets.title')}</h3>
          <span className="badge badge-accent text-[9px] font-mono">{presets.length} ستاپ آماده</span>
          <InfoTooltip
            title="الگوها و استراتژی‌های بهینه‌سازی‌شده آماده"
            text="با کلیک روی هر یک از این ستاپ‌های تست‌شده (مانند Silver Bullet یا Liquidity Sweep)، تمامی تنظیمات فرم، فیلترها و خروج به صورت خودکار بارگذاری می‌شوند."
          />
        </div>
        <span className="text-[10px] text-slate-400 hidden sm:inline">بارگذاری سریع با ۱ کلیک</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {presets.map((preset) => {
          const isSelected = selectedPresetId === preset.id;
          return (
            <button
              key={preset.id}
              type="button"
              onClick={() => onApplyPreset(preset)}
              className={`p-2 rounded-xl border text-right transition-all flex flex-col justify-between group ${
                isSelected
                  ? 'bg-cyan-500/20 border-cyan-500/60 shadow-md shadow-cyan-500/10'
                  : 'bg-slate-900/90 border-white/10 hover:border-cyan-500/40 hover:bg-slate-850'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="badge badge-primary text-[8px] py-0 px-1">{preset.tag}</span>
                  <Sparkles
                    size={11}
                    className={isSelected ? 'text-cyan-400' : 'text-slate-500 group-hover:text-cyan-400 transition-colors'}
                  />
                </div>
                <h4 className="text-[11px] font-bold text-white group-hover:text-cyan-300 transition-colors line-clamp-1">
                  {preset.title}
                </h4>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-white/5 text-[9px] text-cyan-400 font-bold mt-1">
                <span>بارگذاری</span>
                <span className="group-hover:translate-x-[-2px] transition-transform">↵</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
