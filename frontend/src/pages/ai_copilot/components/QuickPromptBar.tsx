import React from 'react';
import { Sparkles } from 'lucide-react';

interface Props {
  onSelectPrompt: (prompt: string) => void;
  selectedSymbol: string;
}

export const QuickPromptBar: React.FC<Props> = ({ onSelectPrompt, selectedSymbol }) => {
  const quickPrompts = [
    `تحلیل فوری وضعیت نماد ${selectedSymbol}`,
    `بررسی ساختار اسمارت مانی (BOS/FVG) در تایم‌فریم ۴ ساعته`,
    `اعتبارسنجی حد ضرر و نسبت سود به ریسک معامله`,
    `پیش‌بینی سناریوهای صعودی و نزولی بر اساس جریان سفارشات`,
  ];

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
      <span className="text-[11px] text-slate-400 shrink-0 flex items-center gap-1">
        <Sparkles size={13} className="text-cyan-400" />
        <span>پرامپت‌های سریع:</span>
      </span>
      {quickPrompts.map((p, idx) => (
        <button
          key={idx}
          type="button"
          onClick={() => onSelectPrompt(p)}
          className="px-3 py-1.5 rounded-xl bg-slate-900/80 border border-white/10 hover:border-cyan-500/40 text-slate-300 hover:text-white text-[11px] shrink-0 transition-all"
        >
          {p}
        </button>
      ))}
    </div>
  );
};
