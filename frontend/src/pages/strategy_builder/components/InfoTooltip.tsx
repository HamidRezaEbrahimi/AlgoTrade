import React from 'react';
import { HelpCircle } from 'lucide-react';

interface Props {
  text: string;
  title?: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export const InfoTooltip: React.FC<Props> = ({ text, title, position = 'top' }) => {
  const getPositionClass = () => {
    switch (position) {
      case 'bottom':
        return 'top-full mt-2 right-1/2 translate-x-1/2';
      case 'left':
        return 'right-full mr-2 top-1/2 -translate-y-1/2';
      case 'right':
        return 'left-full ml-2 top-1/2 -translate-y-1/2';
      case 'top':
      default:
        return 'bottom-full mb-2 right-1/2 translate-x-1/2';
    }
  };

  return (
    <div
      className="relative inline-flex items-center group cursor-pointer"
      onClick={(e) => {
        e.stopPropagation();
        e.preventDefault();
      }}
      onMouseDown={(e) => {
        e.stopPropagation();
      }}
    >
      <HelpCircle
        size={13}
        className="text-slate-400 group-hover:text-cyan-400 transition-colors mx-1 shrink-0"
      />

      <div
        className={`absolute z-50 w-64 p-3 rounded-xl bg-slate-900/95 border border-cyan-500/40 backdrop-blur-md shadow-2xl text-right pointer-events-none transition-all duration-200 opacity-0 group-hover:opacity-100 group-hover:pointer-events-auto scale-95 group-hover:scale-100 ${getPositionClass()}`}
        dir="rtl"
      >
        {title && (
          <div className="text-[11px] font-bold text-cyan-300 border-b border-white/10 pb-1 mb-1.5 flex items-center justify-between">
            <span>{title}</span>
            <span className="text-[9px] text-slate-400 font-mono">راهنما</span>
          </div>
        )}
        <p className="text-[10px] text-slate-200 leading-relaxed font-sans">{text}</p>
      </div>
    </div>
  );
};
