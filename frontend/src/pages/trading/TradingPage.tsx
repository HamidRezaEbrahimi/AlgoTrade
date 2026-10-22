import React, { useState } from 'react';
import { Network } from 'lucide-react';
import { useMarketStore } from '../../stores/useMarketStore';
import { useAppStore } from '../../stores/useAppStore';
import { CandlestickChart } from '../../components/chart/CandlestickChart';
import { ChartLayersToolbar } from '../../components/chart/ChartLayersToolbar';
import { ChartLayerVisibility, DetectorConfig, PatternMarker } from './types';
import { CriteriaScoreCards } from './components/CriteriaScoreCards';
import { OrderEntryModal } from './components/OrderEntryModal';
import { SymbolSearchModal } from './components/SymbolSearchModal';
import { ChartSignalHud } from './components/ChartSignalHud';
import { ChartDrawingToolbar } from './components/ChartDrawingToolbar';
import { PatternSettingsModal } from './components/PatternSettingsModal';
import { PatternDetailDrawer } from './components/PatternDetailDrawer';
import { BarReplayToolbar } from './components/BarReplayToolbar';
import { useTradingMarketData } from './hooks/useTradingMarketData';
import { useBarReplay } from './hooks/useBarReplay';

export const TradingPage: React.FC = () => {
  const { activeSymbol, setActiveSymbol, activeTimeframe, setActiveTimeframe, candles } =
    useMarketStore();
  const { setActivePage } = useAppStore();

  const [selectedExchange, setSelectedExchange] = useState<'wallex' | 'nobitex' | 'faraz'>('wallex');
  const [isOrderModalOpen, setIsOrderModalOpen] = useState<boolean>(false);
  const [isSymbolSearchOpen, setIsSymbolSearchOpen] = useState<boolean>(false);
  const [isPatternSettingsOpen, setIsPatternSettingsOpen] = useState<boolean>(false);
  const [inspectedPattern, setInspectedPattern] = useState<PatternMarker | null>(null);
  const [selectedPatternId, setSelectedPatternId] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const [detectorConfig, setDetectorConfig] = useState<DetectorConfig>({
    min_impulse_atr: 1.5,
    flag_max_retrace: 0.382,
    flat_max_retrace: 0.70,
    wave_b_min_retrace: 0.25,
    min_risk_reward: 1.5,
  });

  const [layersVisibility, setLayersVisibility] = useState<ChartLayerVisibility>({
    tradeSetup: true,
    regularFlat: false,
    expandedFlat: false,
    runningFlat: true,
    contractFlat: false,
    complexFlat: false,
    flags: false,
    smcLevels: false,
    srLevels: false,
    // Context filters
    filterChochBos: false,
    filterVolume: false,
    filterRsi: false,
    filterTrend: false,
  });

  const [focusTimestamp, setFocusTimestamp] = useState<number | null>(null);

  const {
    symbolsList,
    currentPrice,
    isWsConnected,
    isLoadingMore,
    analysis,
    handleLoadMoreHistory,
  } = useTradingMarketData({
    selectedExchange,
    detectorConfig,
  });

  const replay = useBarReplay({
    candles,
    symbol: activeSymbol,
    timeframe: activeTimeframe,
    detectorConfig,
  });

  const displayedCandles = replay.isReplayMode ? replay.visibleCandles : candles;
  const displayedAnalysis = replay.isReplayMode ? (replay.replayAnalysis || analysis) : analysis;
  const displayedPrice =
    replay.isReplayMode && replay.visibleCandles.length > 0
      ? replay.visibleCandles[replay.visibleCandles.length - 1].close
      : currentPrice;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-start">
        {/* Main Chart with Integrated HUD (9 cols or full screen) */}
        <div
          className={
            isFullscreen
              ? 'fixed inset-0 z-50 bg-[#090d16] flex flex-col h-screen w-screen overflow-hidden select-none'
              : 'lg:col-span-9 space-y-3'
          }
        >
          <div
            className={`border border-white/10 overflow-hidden flex flex-col shadow-2xl bg-[#0d1322]/90 ${
              isFullscreen ? 'h-full w-full rounded-none' : 'glass-panel rounded-2xl'
            }`}
          >
            {/* Integrated Top HUD */}
            <ChartSignalHud
              symbol={activeSymbol}
              exchange={selectedExchange}
              currentPrice={displayedPrice}
              selectedTf={activeTimeframe}
              onSelectTf={setActiveTimeframe}
              onOpenSymbolSearch={() => setIsSymbolSearchOpen(true)}
              analysis={displayedAnalysis}
              isFullscreen={isFullscreen}
              onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
              onOpenOrderModal={() => setIsOrderModalOpen(true)}
              isWsConnected={isWsConnected}
              isLoadingMore={isLoadingMore}
              isReplayMode={replay.isReplayMode}
              onToggleReplay={() => {
                if (replay.isReplayMode) {
                  replay.exitReplay();
                } else {
                  replay.startReplay();
                }
              }}
            />

            {/* TradingView-style Bar Replay Floating Toolbar */}
            <BarReplayToolbar replay={replay} totalCandles={candles} />

            {/* Layer Visibility Toolbar */}
            <ChartLayersToolbar
              layers={layersVisibility}
              onChangeLayers={setLayersVisibility}
              patternsCount={displayedAnalysis.detected_patterns?.length || 0}
              patternsList={displayedAnalysis.detected_patterns || []}
            />

            {/* Chart Area with Left Drawing Toolbar */}
            <div className={`flex w-full relative ${isFullscreen ? 'flex-1 h-full' : 'h-[650px]'}`}>
              <ChartDrawingToolbar />
              <div className="flex-1 h-full relative p-1">
                <CandlestickChart
                  candles={displayedCandles}
                  symbol={activeSymbol}
                  timeframe={activeTimeframe}
                  showOrderLines={true}
                  layers={layersVisibility}
                  patterns={displayedAnalysis.detected_patterns || []}
                  levels={displayedAnalysis.levels}
                  tradeSetup={displayedAnalysis.trade_setup}
                  focusTimestamp={focusTimestamp}
                  selectedPatternId={selectedPatternId}
                  onSelectPattern={(pat) => {
                    setSelectedPatternId((prev) => (pat ? (prev === pat.id ? null : pat.id) : null));
                  }}
                  isFullscreen={isFullscreen}
                  onLoadMoreHistory={handleLoadMoreHistory}
                  onChartClick={(ts) => {
                    if (replay.isReplayMode && replay.isCutting) {
                      replay.jumpToTime(ts);
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Analysis & Risk Sidebar (3 cols - Left side in RTL - hidden when fullscreen) */}
        {!isFullscreen && (
          <div className="lg:col-span-3 space-y-2.5">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setActivePage('ai_optimizer')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20 text-xs transition-colors"
                title="ورود به استودیو مدیریت و ویرایش قواعد الگوها"
              >
                <Network size={14} />
                <span>فرمول الگوها</span>
              </button>
              <button
                type="button"
                onClick={() => setIsPatternSettingsOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 text-xs transition-colors"
              >
                تنظیمات الگو
              </button>
            </div>
            <CriteriaScoreCards
              analysis={displayedAnalysis}
              currentPrice={displayedPrice}
              selectedPatternId={selectedPatternId}
              onFocusPattern={(ts, pat) => {
                if (ts) setFocusTimestamp(ts);
                setSelectedPatternId((prev) => (pat ? (prev === pat.id ? null : pat.id) : null));
              }}
              onOpenSettings={() => setIsPatternSettingsOpen(true)}
              onInspectPattern={(pat) => setInspectedPattern(pat)}
            />
          </div>
        )}
      </div>

      {/* Pattern Settings Modal */}
      <PatternSettingsModal
        isOpen={isPatternSettingsOpen}
        onClose={() => setIsPatternSettingsOpen(false)}
        config={detectorConfig}
        onSaveConfig={(newCfg) => setDetectorConfig(newCfg)}
      />

      {/* Pattern Deep Inspection Drawer */}
      <PatternDetailDrawer
        pattern={inspectedPattern}
        onClose={() => setInspectedPattern(null)}
      />

      {/* Unified Symbol Search Modal */}
      <SymbolSearchModal
        isOpen={isSymbolSearchOpen}
        onClose={() => setIsSymbolSearchOpen(false)}
        symbols={symbolsList}
        selectedSymbol={activeSymbol}
        selectedExchange={selectedExchange}
        onSelectSymbol={setActiveSymbol}
        onSelectExchange={setSelectedExchange}
      />

      {/* Safety Order Modal */}
      <OrderEntryModal
        isOpen={isOrderModalOpen}
        onClose={() => setIsOrderModalOpen(false)}
        symbol={activeSymbol}
        currentPrice={currentPrice}
      />
    </div>
  );
};
