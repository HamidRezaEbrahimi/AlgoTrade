import React from 'react';
import {
  Layers,
  Target,
  Boxes,
  Eye,
  EyeOff,
} from 'lucide-react';
import { ChartLayerVisibility, PatternMarker } from '../../pages/trading/types';

interface Props {
  layers: ChartLayerVisibility;
  onChangeLayers: (updated: ChartLayerVisibility) => void;
  patternsCount?: number;
  patternsList?: PatternMarker[];
  onFocusPattern?: (time: number) => void;
}

export const ChartLayersToolbar: React.FC<Props> = ({
  layers,
  onChangeLayers,
  patternsList = [],
}) => {
  const toggle = (key: keyof ChartLayerVisibility) => {
    onChangeLayers({
      ...layers,
      [key]: !layers[key],
    });
  };

  const isAllActive = layers.tradeSetup && layers.runningFlat;

  const toggleAll = () => {
    const nextState = !isAllActive;
    onChangeLayers({
      ...layers,
      tradeSetup: nextState,
      runningFlat: nextState,
      smcLevels: nextState,
      srLevels: nextState,
    });
  };

  const runFlatCount = patternsList.filter((p) => p.id?.startsWith('running_flat') && !(p as any).is_developing).length;
  const devPrzCount = patternsList.filter((p) => (p as any).is_developing || p.id?.startsWith('developing_prz')).length;

  return (
    <div className="flex flex-wrap items-center justify-between gap-1.5 p-1.5 bg-[#090d16]/95 backdrop-blur-md border-b border-white/10 text-xs select-none">
      <div className="flex items-center gap-1.5 flex-wrap">
        <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-slate-300 font-bold ml-1">
          <Layers size={13} className="text-cyan-400" />
          <span>لایه‌های AlefTrade:</span>
        </div>

        {/* 1. Trade Setup Toggle */}
        <button
          type="button"
          onClick={() => toggle('tradeSetup')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-bold transition-all border ${
            layers.tradeSetup
              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-sm shadow-cyan-500/10'
              : 'bg-white/5 text-slate-400 border-transparent hover:text-white hover:bg-white/10'
          }`}
          title="نمایش خطوط ورود، حد ضرر (SL) و تارگت‌های سود (TP) متصل به پلن معاملاتی AlefTrade"
        >
          <Target size={12} className={layers.tradeSetup ? 'text-cyan-400' : 'text-slate-500'} />
          <span>ست‌آپ معامله</span>
        </button>

        {/* 2. Running Flat Toggle */}
        <button
          type="button"
          onClick={() => toggle('runningFlat')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg font-bold transition-all border ${
            layers.runningFlat
              ? 'bg-purple-500/20 text-purple-300 border-purple-500/40 shadow-sm shadow-purple-500/10'
              : 'bg-white/5 text-slate-400 border-transparent hover:text-white hover:bg-white/10'
          }`}
          title="نمایش امواج ۵ نقطه‌ای رانینگ فلت الیوت (0-1-A-B-C)"
        >
          <Boxes size={12} className={layers.runningFlat ? 'text-purple-400' : 'text-slate-500'} />
          <span>امواج رانینگ فلت (0-1-A-B-C)</span>
          {runFlatCount > 0 && (
            <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${layers.runningFlat ? 'bg-purple-400 text-slate-950' : 'bg-white/10 text-slate-400'}`}>
              {runFlatCount}
            </span>
          )}
        </button>

        {/* 3. Developing PRZ Zone Indicator */}
        {devPrzCount > 0 && (
          <div
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm shadow-amber-500/10"
            title="منطقه بازگشت احتمالی موج C در حال شکل‌گیری (AlefTrade PRZ)"
          >
            <Boxes size={12} className="text-amber-400" />
            <span>منطقه شکار PRZ</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold bg-amber-400 text-slate-950">
              {devPrzCount}
            </span>
          </div>
        )}
      </div>

      {/* Master Toggle All Button */}
      <button
        type="button"
        onClick={toggleAll}
        className="flex items-center gap-1 px-2 py-1 rounded-lg text-slate-400 hover:text-white bg-white/5 hover:bg-white/10 transition-colors border border-white/5 shrink-0"
      >
        {isAllActive ? <EyeOff size={12} /> : <Eye size={12} />}
        <span>{isAllActive ? 'مخفی‌سازی همه' : 'نمایش همه'}</span>
      </button>
    </div>
  );
};
