import React, { useState } from 'react';
import {
  Crosshair,
  TrendingUp,
  Minus,
  Ruler,
  Trash2,
  Lock,
  Layers,
} from 'lucide-react';

export const ChartDrawingToolbar: React.FC = () => {
  const [activeTool, setActiveTool] = useState<string>('crosshair');

  const tools = [
    { id: 'crosshair', icon: Crosshair, title: 'نشانگر کراس‌هیر (Crosshair)' },
    { id: 'trendline', icon: TrendingUp, title: 'خط روند (Trend Line)' },
    { id: 'horizontal', icon: Minus, title: 'سطح افقی حمایت/مقاومت (Horizontal Level)' },
    { id: 'ruler', icon: Ruler, title: 'خط‌کش درصد تغییر قیمت (Measure)' },
    { id: 'levels', icon: Layers, title: 'لایه‌های ساختار و نقدینگی (SMC Zones)' },
  ];

  return (
    <div className="flex flex-col items-center gap-1.5 p-1.5 bg-[#090d16]/95 backdrop-blur-md border-r border-white/10 select-none">
      {tools.map((t) => {
        const Icon = t.icon;
        const isActive = activeTool === t.id;
        return (
          <button
            key={t.id}
            type="button"
            title={t.title}
            onClick={() => setActiveTool(t.id)}
            className={`p-2 rounded-xl transition-all ${
              isActive
                ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Icon size={16} />
          </button>
        );
      })}

      <div className="w-4 h-[1px] bg-white/10 my-1" />

      <button
        type="button"
        title="قفل ابزارها"
        className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-all"
      >
        <Lock size={15} />
      </button>

      <button
        type="button"
        title="پاکسازی ترسیمات"
        onClick={() => setActiveTool('crosshair')}
        className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
      >
        <Trash2 size={15} />
      </button>
    </div>
  );
};
