import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Play,
  RotateCcw,
  CheckCircle2,
  Layers,
  Activity,
  Shield,
  Sparkles,
  ArrowRight,
  ArrowLeft,
} from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';
import { STRATEGY_PRESETS } from './presets';
import { useStrategyBuilder } from './useStrategyBuilder';
import { PresetLibrary } from './components/PresetLibrary';
import { IdentityStep } from './components/IdentityStep';
import { PatternLayer } from './components/PatternLayer';
import { IndicatorLayer } from './components/IndicatorLayer';
import { AiGateLayer } from './components/AiGateLayer';
import { ExitRiskLayer } from './components/ExitRiskLayer';
import { SavedStrategiesGrid } from './components/SavedStrategiesGrid';
import { StrategyLivePreview } from './components/StrategyLivePreview';

export const StrategyBuilderPage: React.FC = () => {
  const { t, i18n } = useTranslation(['StrategyBuilder', 'Common']);
  const isRtl = i18n.language === 'fa';
  const { setActivePage } = useAppStore();

  const {
    activeTab,
    setActiveTab,
    selectedPresetId,
    savedStrategies,
    loading,
    saveStatus,
    strategyName,
    setStrategyName,
    strategyKey,
    setStrategyKey,
    structureTf,
    setStructureTf,
    entryTf,
    setEntryTf,
    filterTf,
    setFilterTf,
    chkBos,
    setChkBos,
    chkOb,
    setChkOb,
    chkFvg,
    setChkFvg,
    chkSr,
    setChkSr,
    chkFlag,
    setChkFlag,
    chkFlat,
    setChkFlat,
    chkWedge,
    setChkWedge,
    chkEngulfing,
    setChkEngulfing,
    chkPinbar,
    setChkPinbar,
    chkHammer,
    setChkHammer,
    chkMorningStar,
    setChkMorningStar,
    rsiMin,
    setRsiMin,
    rsiMax,
    setRsiMax,
    chkVolumeMa,
    setChkVolumeMa,
    chkAiConfirmation,
    setChkAiConfirmation,
    minScore,
    setMinScore,
    slType,
    setSlType,
    minRiskReward,
    setMinRiskReward,
    tp1Ratio,
    setTp1Ratio,
    tp2Ratio,
    setTp2Ratio,
    activePatternsCount,
    applyPreset,
    handleSaveStrategy,
  } = useStrategyBuilder();

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 glass-panel p-4 border border-white/10 rounded-2xl">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles size={20} className="text-cyan-400" />
            <span>{t('StrategyBuilder:header.title')}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('StrategyBuilder:header.subtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActivePage('backtest')}
            className="btn btn-sm btn-ghost border border-white/10 text-slate-300 hover:text-white"
          >
            <Play size={14} className="text-emerald-400" />
            <span>{t('StrategyBuilder:header.btn_backtest')}</span>
          </button>
          <button
            type="button"
            onClick={handleSaveStrategy}
            className="btn btn-sm btn-primary shadow-lg shadow-cyan-500/20 gap-1.5"
          >
            <RotateCcw size={14} />
            <span>{t('StrategyBuilder:header.btn_save')}</span>
          </button>
        </div>
      </div>

      {saveStatus && (
        <div className="alert alert-success text-xs py-2 px-4 flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>استراتژی با موفقیت ذخیره و در ریجستری فعال شد.</span>
        </div>
      )}

      {/* TOP SECTION: Side-by-Side Presets Library & Live Preview Blueprint */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        <div className="lg:col-span-8">
          <PresetLibrary
            presets={STRATEGY_PRESETS}
            onApplyPreset={applyPreset}
            selectedPresetId={selectedPresetId}
          />
        </div>
        <div className="lg:col-span-4">
          <StrategyLivePreview
            strategyName={strategyName}
            strategyKey={strategyKey}
            structureTf={structureTf}
            entryTf={entryTf}
            filterTf={filterTf}
            minScore={minScore}
            minRiskReward={minRiskReward}
            tp1Ratio={tp1Ratio}
            tp2Ratio={tp2Ratio}
            chkAiConfirmation={chkAiConfirmation}
            activePatternsCount={activePatternsCount}
          />
        </div>
      </div>

      {/* TAB NAVIGATION BAR */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-900/90 p-1.5 rounded-2xl border border-white/10">
        <button
          type="button"
          onClick={() => setActiveTab('patterns')}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'patterns'
              ? 'bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20 font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Layers size={15} />
          <span>{t('StrategyBuilder:tabs.tab_patterns')}</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('indicators')}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'indicators'
              ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/20 font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Activity size={15} />
          <span>{t('StrategyBuilder:tabs.tab_indicators')}</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('risk')}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'risk'
              ? 'bg-amber-500 text-slate-950 shadow-lg shadow-amber-500/20 font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Shield size={15} />
          <span>{t('StrategyBuilder:tabs.tab_risk')}</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('registry')}
          className={`py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
            activeTab === 'registry'
              ? 'bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20 font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <Sparkles size={15} />
          <span>{t('StrategyBuilder:tabs.tab_registry')}</span>
        </button>
      </div>

      {/* TAB CONTENT */}
      {activeTab === 'patterns' && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
            <div className="lg:col-span-4">
              <IdentityStep
                strategyName={strategyName}
                setStrategyName={setStrategyName}
                strategyKey={strategyKey}
                setStrategyKey={setStrategyKey}
                structureTf={structureTf}
                setStructureTf={setStructureTf}
                entryTf={entryTf}
                setEntryTf={setEntryTf}
                filterTf={filterTf}
                setFilterTf={setFilterTf}
              />
            </div>
            <div className="lg:col-span-8">
              <PatternLayer
                chkBos={chkBos}
                setChkBos={setChkBos}
                chkOb={chkOb}
                setChkOb={setChkOb}
                chkFvg={chkFvg}
                setChkFvg={setChkFvg}
                chkSr={chkSr}
                setChkSr={setChkSr}
                chkFlag={chkFlag}
                setChkFlag={setChkFlag}
                chkFlat={chkFlat}
                setChkFlat={setChkFlat}
                chkWedge={chkWedge}
                setChkWedge={setChkWedge}
                chkEngulfing={chkEngulfing}
                setChkEngulfing={setChkEngulfing}
                chkPinbar={chkPinbar}
                setChkPinbar={setChkPinbar}
                chkHammer={chkHammer}
                setChkHammer={setChkHammer}
                chkMorningStar={chkMorningStar}
                setChkMorningStar={setChkMorningStar}
              />
            </div>
          </div>
          <div className="flex justify-end pt-1">
            <button
              type="button"
              onClick={() => setActiveTab('indicators')}
              className="btn btn-sm btn-primary gap-2"
            >
              <span>{t('StrategyBuilder:tabs.btn_next')}</span>
              {isRtl ? <ArrowLeft size={14} /> : <ArrowRight size={14} />}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'indicators' && (
        <div className="space-y-4">
          <IndicatorLayer
            rsiMin={rsiMin}
            setRsiMin={setRsiMin}
            rsiMax={rsiMax}
            setRsiMax={setRsiMax}
            chkVolumeMa={chkVolumeMa}
            setChkVolumeMa={setChkVolumeMa}
            minScore={minScore}
            setMinScore={setMinScore}
          />
          <AiGateLayer
            chkAiConfirmation={chkAiConfirmation}
            setChkAiConfirmation={setChkAiConfirmation}
          />
          <div className="flex justify-between pt-1">
            <button
              type="button"
              onClick={() => setActiveTab('patterns')}
              className="btn btn-sm btn-ghost border border-white/10 text-slate-300 gap-2"
            >
              {isRtl ? <ArrowRight size={14} /> : <ArrowLeft size={14} />}
              <span>{t('StrategyBuilder:tabs.btn_prev')}</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('risk')}
              className="btn btn-sm btn-primary gap-2"
            >
              <span>{t('StrategyBuilder:tabs.btn_next')}</span>
              {isRtl ? <ArrowLeft size={14} /> : <ArrowRight size={14} />}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'risk' && (
        <div className="space-y-4">
          <ExitRiskLayer
            slType={slType}
            setSlType={setSlType}
            minRiskReward={minRiskReward}
            setMinRiskReward={setMinRiskReward}
            tp1Ratio={tp1Ratio}
            setTp1Ratio={setTp1Ratio}
            tp2Ratio={tp2Ratio}
            setTp2Ratio={setTp2Ratio}
          />
          <div className="flex justify-between pt-1">
            <button
              type="button"
              onClick={() => setActiveTab('indicators')}
              className="btn btn-sm btn-ghost border border-white/10 text-slate-300 gap-2"
            >
              {isRtl ? <ArrowRight size={14} /> : <ArrowLeft size={14} />}
              <span>{t('StrategyBuilder:tabs.btn_prev')}</span>
            </button>
            <button
              type="button"
              onClick={handleSaveStrategy}
              className="btn btn-sm btn-success text-slate-950 font-bold gap-2"
            >
              <CheckCircle2 size={15} />
              <span>{t('StrategyBuilder:header.btn_save')}</span>
            </button>
          </div>
        </div>
      )}

      {activeTab === 'registry' && (
        <div className="space-y-4">
          <SavedStrategiesGrid strategies={savedStrategies} loading={loading} />
        </div>
      )}
    </div>
  );
};
