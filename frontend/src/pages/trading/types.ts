export interface WavePoint {
  label: string;
  time: number;
  price: number;
}

export interface TradeZoneLevel {
  price: number;
  label: string;
  label_en: string;
}

export interface PatternTradeZones {
  entry_a: TradeZoneLevel;
  entry_b: TradeZoneLevel;
  stop_loss: TradeZoneLevel;
  tp1: TradeZoneLevel;
  tp2: TradeZoneLevel;
}

export interface ContextTag {
  key: string;
  label: string;
  label_en: string;
  passed: boolean;
  value: string;
}

export interface ProgressiveStage {
  step: number;
  name: string;
  status: 'COMPLETED' | 'ACTIVE' | 'READY_TO_TRIGGER' | 'PENDING' | string;
  detail: string;
  passed: boolean;
}

export interface PatternMarker {
  id: string;
  time: number;
  type: string;
  name: string;
  name_en?: string;
  category?: 'flat' | 'flag' | 'wedge' | 'candlestick' | string;
  direction: 'bullish' | 'bearish';
  price: number;
  confidence: number;
  position: 'belowBar' | 'aboveBar';
  color: string;
  pattern_color?: string;
  shape: 'arrowUp' | 'arrowDown' | 'circle' | 'square';
  text: string;
  points?: WavePoint[];
  metrics?: Record<string, any>;
  rules_evaluation?: Array<{
    rule: string;
    condition?: string;
    passed: boolean;
    value: string;
  }>;
  // Live progressive wave tracking & dual probabilities
  is_developing?: boolean;
  lifecycle_status?: 'ACTIVE' | 'INVALIDATED' | 'TARGET_HIT';
  is_invalidated?: boolean;
  is_target_hit?: boolean;
  invalidation_reason?: string;
  stage?: string;
  stage_label?: string;
  status_text?: string;
  pattern_probability?: number;
  trade_win_probability?: number;
  quality_score?: number;
  quality_grade?: 'STRONG' | 'NORMAL' | 'WEAK';
  grade_color?: string;
  quality_strengths?: string[];
  quality_cautions?: string[];
  quality_breakdown?: Record<string, number>;
  progressive_stages?: ProgressiveStage[];
  prz_zone?: {
    top: number;
    bottom: number;
    start_time: number;
    end_time: number;
    label: string;
  };
  // New v2: per-pattern trade zones
  trade_zones?: PatternTradeZones;
  // New v2: context filter tags (CHoCH, Volume, RSI, Trend)
  context_tags?: ContextTag[];
  // Legacy trade_setup (backward compatible)
  trade_setup?: {
    entry?: number;
    entry_price?: number;
    stop_loss: number;
    take_profit_1: number;
    take_profit_2: number;
    risk_reward_ratio: number;
    signal?: 'BUY' | 'SELL' | 'WAIT';
    is_live_entry?: boolean;
    pattern_name?: string | null;
  };
}

export interface DetectorConfig {
  min_impulse_atr: number;
  flag_max_retrace: number;
  flat_max_retrace: number;
  wave_b_min_retrace: number;
  min_risk_reward: number;
}

export interface ChartLayerVisibility {
  tradeSetup: boolean; // Entry / SL / TP lines
  regularFlat: boolean;
  expandedFlat: boolean;
  runningFlat: boolean;
  contractFlat: boolean;
  complexFlat: boolean;
  flags: boolean; // Bullish & Bearish Flags
  smcLevels: boolean; // Order Block & FVG levels
  srLevels: boolean; // Support & Resistance lines
  // Context filter toggles (v2)
  filterChochBos: boolean;
  filterVolume: boolean;
  filterRsi: boolean;
  filterTrend: boolean;
}

export interface CriteriaResult {
  passed: boolean;
  score: number;
  max_score: number;
  rsi?: number;
  atr?: number;
  volume?: number;
  volume_ma10?: number;
  current_price?: number;
  change_24h?: number;
  pattern_probability?: number;
  trade_win_probability?: number;
  progressive_stages?: ProgressiveStage[];
  is_developing?: boolean;
  stage?: string;
  stage_label?: string;
  criteria: {
    structure_4h: boolean;
    location_valid: boolean;
    pattern_1h: boolean;
    momentum_15m: boolean;
    rsi_confirmed: boolean;
    volume_confirmed: boolean;
    rr_valid: boolean;
    stop_loss_valid: boolean;
  };
  detected_patterns?: PatternMarker[];
  levels?: {
    order_block_demand?: number;
    fvg_imbalance?: number;
    support_level?: number;
    resistance_level?: number;
  };
  trade_setup?: {
    entry_price: number;
    stop_loss: number;
    take_profit_1: number;
    take_profit_2: number;
    risk_reward_ratio: number;
    signal: 'BUY' | 'SELL' | 'WAIT';
    is_live_entry?: boolean;
    pattern_name?: string | null;
  };
  details?: Record<string, any>;
}

export interface SymbolMeta {
  symbol: string;
  raw_symbol?: string;
  name: string;
  name_en?: string;
  base?: string;
  quote?: string;
  exchange?: 'wallex' | 'nobitex' | 'faraz';
  type: 'crypto' | 'gold_forex' | 'toman';
  price: number;
  change24h: number;
}
