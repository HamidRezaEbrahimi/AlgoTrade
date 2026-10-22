import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Play, BarChart3 } from 'lucide-react';
import axios from 'axios';

interface StrategyOption {
  key: string;
  name_fa: string;
  name_en: string;
  family: string;
}

export const BacktestRunner: React.FC = () => {
  const { t } = useTranslation('Backtest');
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [strategyKey, setStrategyKey] = useState('price_action_8criteria');
  const [strategies, setStrategies] = useState<StrategyOption[]>([]);
  const [capital, setCapital] = useState(10000);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const res = await axios.get('/api/strategies');
        setStrategies(res.data);
      } catch (e) {
        console.error('Failed to load strategies list', e);
      }
    };
    loadStrategies();
  }, []);

  const handleRun = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/backtest/run', {
        symbol,
        strategy_key: strategyKey,
        initial_capital: capital,
        fee_rate: 0.001,
        slippage_rate: 0.0005,
      });
      setResult(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="text-cyan-400" size={22} />
          <span>{t('title')}</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">{t('subtitle')}</p>
      </div>

      {/* Input Parameters */}
      <div className="glass-panel p-5 grid grid-cols-1 sm:grid-cols-5 gap-4 items-end">
        <div>
          <label className="block text-xs text-slate-400 mb-1.5">استراتژی معاملاتی</label>
          <select
            value={strategyKey}
            onChange={(e) => setStrategyKey(e.target.value)}
            className="w-full bg-slate-900 border border-white/10 rounded px-3 py-2 text-sm text-white font-mono"
          >
            {strategies.length > 0 ? (
              strategies.map((st) => (
                <option key={st.key} value={st.key}>
                  {st.name_fa} ({st.key})
                </option>
              ))
            ) : (
              <option value="price_action_8criteria">پرایس‌اکشن ۸ معیاره</option>
            )}
          </select>
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1.5">{t('symbol')}</label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="w-full bg-slate-900 border border-white/10 rounded px-3 py-2 text-sm text-white font-mono"
          >
            <option value="BTCUSDT">BTC/USDT</option>
            <option value="ETHUSDT">ETH/USDT</option>
            <option value="SOLUSDT">SOL/USDT</option>
          </select>
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1.5">{t('initial_capital')}</label>
          <input
            type="number"
            value={capital}
            onChange={(e) => setCapital(Number(e.target.value))}
            className="w-full bg-slate-900 border border-white/10 rounded px-3 py-2 text-sm text-white font-mono"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1.5">{t('fee_rate')}</label>
          <input
            type="text"
            disabled
            value="0.10% (Maker/Taker)"
            className="w-full bg-slate-900/50 border border-white/5 rounded px-3 py-2 text-sm text-slate-400 font-mono"
          />
        </div>

        <button
          type="button"
          onClick={handleRun}
          disabled={loading}
          className="btn btn-primary h-[38px] w-full"
        >
          <Play size={16} />
          <span>{loading ? t('running') : t('run_button')}</span>
        </button>
      </div>

      {/* Results Display */}
      {result && (
        <div className="space-y-6">
          <div className="dashboard-grid">
            <div className="glass-panel p-4">
              <span className="text-xs text-slate-400">{t('win_rate')}</span>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {result.metrics.win_rate_pct}%
              </div>
            </div>

            <div className="glass-panel p-4">
              <span className="text-xs text-slate-400">{t('profit_factor')}</span>
              <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
                {result.metrics.profit_factor}
              </div>
            </div>

            <div className="glass-panel p-4">
              <span className="text-xs text-slate-400">{t('max_drawdown')}</span>
              <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
                {result.metrics.max_drawdown_pct}%
              </div>
            </div>

            <div className="glass-panel p-4">
              <span className="text-xs text-slate-400">{t('total_pnl')}</span>
              <div className="text-2xl font-bold font-mono text-white mt-1">
                ${result.metrics.total_pnl}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
