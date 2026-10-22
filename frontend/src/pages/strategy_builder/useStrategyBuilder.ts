import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { StrategyItem, PresetTemplate } from './types';

export const useStrategyBuilder = () => {
  const [activeTab, setActiveTab] = useState<'patterns' | 'indicators' | 'risk' | 'registry'>('patterns');
  const [selectedPresetId, setSelectedPresetId] = useState<string>('preset_ict_silver_bullet');
  const [savedStrategies, setSavedStrategies] = useState<StrategyItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Form states
  const [strategyName, setStrategyName] = useState<string>('گلوله نقره‌ای ICT سشن بعدازظهر');
  const [strategyKey, setStrategyKey] = useState<string>('ict_silver_bullet_pm');
  const [structureTf, setStructureTf] = useState<string>('4h');
  const [entryTf, setEntryTf] = useState<string>('1h');
  const [filterTf, setFilterTf] = useState<string>('15m');

  // Pattern states
  const [chkBos, setChkBos] = useState<boolean>(true);
  const [chkOb, setChkOb] = useState<boolean>(true);
  const [chkFvg, setChkFvg] = useState<boolean>(true);
  const [chkSr, setChkSr] = useState<boolean>(true);
  const [chkFlag, setChkFlag] = useState<boolean>(false);
  const [chkFlat, setChkFlat] = useState<boolean>(false);
  const [chkWedge, setChkWedge] = useState<boolean>(false);
  const [chkEngulfing, setChkEngulfing] = useState<boolean>(true);
  const [chkPinbar, setChkPinbar] = useState<boolean>(true);
  const [chkHammer, setChkHammer] = useState<boolean>(false);
  const [chkMorningStar, setChkMorningStar] = useState<boolean>(false);

  // Indicator & AI states
  const [rsiMin, setRsiMin] = useState<number>(40);
  const [rsiMax, setRsiMax] = useState<number>(70);
  const [chkVolumeMa, setChkVolumeMa] = useState<boolean>(true);
  const [chkAiConfirmation, setChkAiConfirmation] = useState<boolean>(true);
  const [minScore, setMinScore] = useState<number>(7);

  // Exit & Risk states
  const [slType, setSlType] = useState<string>('swing_low');
  const [minRiskReward, setMinRiskReward] = useState<number>(2.0);
  const [tp1Ratio, setTp1Ratio] = useState<number>(1.5);
  const [tp2Ratio, setTp2Ratio] = useState<number>(3.0);

  const activePatternsCount = useMemo(() => {
    return (
      (chkFlag ? 1 : 0) +
      (chkFlat ? 1 : 0) +
      (chkWedge ? 1 : 0) +
      (chkBos ? 1 : 0) +
      (chkOb ? 1 : 0) +
      (chkFvg ? 1 : 0) +
      (chkSr ? 1 : 0) +
      (chkEngulfing ? 1 : 0) +
      (chkPinbar ? 1 : 0) +
      (chkHammer ? 1 : 0) +
      (chkMorningStar ? 1 : 0)
    );
  }, [
    chkFlag,
    chkFlat,
    chkWedge,
    chkBos,
    chkOb,
    chkFvg,
    chkSr,
    chkEngulfing,
    chkPinbar,
    chkHammer,
    chkMorningStar,
  ]);

  const applyPreset = (preset: PresetTemplate) => {
    setSelectedPresetId(preset.id);
    const c = preset.config;
    setStrategyName(c.name);
    setStrategyKey(c.key);
    setChkFlag(c.patterns.flag);
    setChkFlat(c.patterns.flat);
    setChkWedge(c.patterns.wedge);
    setChkBos(c.patterns.bos);
    setChkOb(c.patterns.ob);
    setChkFvg(c.patterns.fvg);
    setChkEngulfing(c.candlesticks.engulfing);
    setChkPinbar(c.candlesticks.pinbar);
    setChkHammer(c.candlesticks.hammer);
    setChkMorningStar(c.candlesticks.morning_star);
    setStructureTf(c.timeframes.structure);
    setEntryTf(c.timeframes.entry);
    setFilterTf(c.timeframes.filter);
    setRsiMin(c.rsi.min);
    setRsiMax(c.rsi.max);
    setChkVolumeMa(c.volumeMa);
    setChkAiConfirmation(c.aiConfirmation);
    setMinRiskReward(c.minRr);
    setMinScore(c.minScore);
    setTp1Ratio(c.tp1);
    setTp2Ratio(c.tp2);
  };

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/api/strategies');
      setSavedStrategies(res.data || []);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStrategies();
  }, []);

  const handleSaveStrategy = async () => {
    setSaveStatus(null);
    try {
      const payload = {
        name: strategyName,
        key: strategyKey,
        structure_tf: structureTf,
        entry_tf: entryTf,
        filter_tf: filterTf,
        patterns: {
          flag: chkFlag,
          flat: chkFlat,
          wedge: chkWedge,
          bos: chkBos,
          ob: chkOb,
          fvg: chkFvg,
          sr: chkSr,
        },
        candlesticks: {
          engulfing: chkEngulfing,
          pinbar: chkPinbar,
          hammer: chkHammer,
          morning_star: chkMorningStar,
        },
        indicators: {
          rsi_min: rsiMin,
          rsi_max: rsiMax,
          volume_ma_confirmation: chkVolumeMa,
          min_score: minScore,
        },
        ai_confirmation_required: chkAiConfirmation,
        risk: {
          stop_loss_type: slType,
          min_risk_reward: minRiskReward,
          tp1_ratio: tp1Ratio,
          tp2_ratio: tp2Ratio,
        },
      };

      await axios.post('/api/ai-optimizer/custom-strategy', payload);
      setSaveStatus('success');
      fetchStrategies();
    } catch {
      setSaveStatus('saved_local');
    }
  };

  return {
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
  };
};
