export interface StrategyItem {
  key: string;
  name_fa?: string;
  name_en?: string;
  family?: string;
  is_builtin?: boolean;
}

export interface PresetConfig {
  name: string;
  key: string;
  patterns: {
    flag: boolean;
    flat: boolean;
    wedge: boolean;
    bos: boolean;
    ob: boolean;
    fvg: boolean;
  };
  candlesticks: {
    engulfing: boolean;
    pinbar: boolean;
    hammer: boolean;
    morning_star: boolean;
  };
  timeframes: {
    structure: string;
    entry: string;
    filter: string;
  };
  rsi: {
    min: number;
    max: number;
  };
  volumeMa: boolean;
  aiConfirmation: boolean;
  minRr: number;
  minScore: number;
  tp1: number;
  tp2: number;
}

export interface PresetTemplate {
  id: string;
  title: string;
  tag: string;
  desc: string;
  config: PresetConfig;
}
