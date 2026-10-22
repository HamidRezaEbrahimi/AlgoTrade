export interface DiscoveredPattern {
  pattern_id: string;
  name_fa: string;
  name_en: string;
  category: string;
  timeframe: string;
  occurrences: number;
  win_rate: number;
  profit_factor: number;
  avg_risk_reward: number;
  avg_pnl_pct: number;
  confidence_score: number;
  rules: Record<string, any>;
  description_fa: string;
}

export interface CustomPatternItem {
  id: string;
  name_fa: string;
  name_en: string;
  category: string;
  timeframe: string;
  win_rate_estimate: number;
  profit_factor_estimate: number;
  description_fa?: string;
  rules?: Record<string, any>;
  tags?: string[];
  created_at?: string;
}

export interface OptimizationMetrics {
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_trades: number;
  net_profit_pct: number;
}

export interface OptimizationResponse {
  strategy_key: string;
  initial_params: Record<string, any>;
  optimized_params: Record<string, any>;
  before_metrics: OptimizationMetrics;
  after_metrics: OptimizationMetrics;
  recommendation_fa: string;
  recommendation_en: string;
}

export interface LocalModelStatusData {
  engine_type: string;
  model_name: string;
  is_trained: boolean;
  training_samples: number;
  accuracy_score: number;
  f1_score: number;
  last_trained_at: string;
  ollama_endpoint: string;
  ollama_connected: boolean;
  active_weights: Record<string, number>;
}
