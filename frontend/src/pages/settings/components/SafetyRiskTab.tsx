import React from 'react';
import { useTranslation } from 'react-i18next';
import { Shield, Lock, Unlock, AlertTriangle } from 'lucide-react';

interface Props {
  autoTradingEnabled: boolean;
  onToggleAutoTrading: () => void;
  maxRiskPerTrade: number;
  setMaxRiskPerTrade: (val: number) => void;
  onSaveRiskParams: () => void;
}

export const SafetyRiskTab: React.FC<Props> = ({
  autoTradingEnabled,
  onToggleAutoTrading,
  maxRiskPerTrade,
  setMaxRiskPerTrade,
  onSaveRiskParams,
}) => {
  const { t } = useTranslation(['Settings', 'Common']);

  return (
    <div className="space-y-4">
      {/* Master Kill-Switch / Auto-Trading Box */}
      <div
        className={`glass-panel p-5 border transition-all ${
          autoTradingEnabled
            ? 'border-emerald-500/50 bg-emerald-950/10'
            : 'border-amber-500/40 bg-amber-950/10'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                autoTradingEnabled
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-amber-500/20 text-amber-400'
              }`}
            >
              {autoTradingEnabled ? <Unlock size={20} /> : <Lock size={20} />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white">{t('safety.master_title')}</h3>
                <span
                  className={`badge text-[10px] ${
                    autoTradingEnabled ? 'badge-success' : 'badge-warning'
                  }`}
                >
                  {autoTradingEnabled ? t('safety.auto_enabled') : t('safety.auto_disabled')}
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
                {t('safety.master_desc')}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onToggleAutoTrading}
            className={`btn btn-sm ${
              autoTradingEnabled ? 'btn-error' : 'btn-success text-slate-950 font-bold'
            }`}
          >
            {autoTradingEnabled ? t('safety.btn_lock') : t('safety.btn_unlock')}
          </button>
        </div>
      </div>

      {/* Risk Parameters Form */}
      <div className="glass-panel p-5 space-y-4 text-xs">
        <div className="flex items-center gap-2 border-b border-white/10 pb-3">
          <Shield size={18} className="text-cyan-400" />
          <h3 className="text-sm font-bold text-white">{t('safety.risk_params_title')}</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-slate-300 font-bold mb-1">
              {t('safety.max_risk_label')}
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="5.0"
                value={maxRiskPerTrade}
                onChange={(e) => setMaxRiskPerTrade(Number(e.target.value))}
                className="w-24 bg-slate-900 border border-white/10 rounded-lg p-2 text-center text-white font-bold"
              />
              <span className="text-slate-400 text-xs">{t('safety.max_risk_hint')}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5 space-y-1">
            <h4 className="font-bold text-amber-400 flex items-center gap-1.5">
              <AlertTriangle size={14} />
              <span>{t('safety.circuit_title')}</span>
            </h4>
            <p className="text-[11px] text-slate-300">{t('safety.circuit_8')}</p>
            <p className="text-[11px] text-slate-300">{t('safety.circuit_12')}</p>
          </div>
        </div>

        <div className="pt-3 border-t border-white/10 flex justify-end">
          <button type="button" onClick={onSaveRiskParams} className="btn btn-sm btn-primary">
            {t('header.btn_save_safety')}
          </button>
        </div>
      </div>
    </div>
  );
};
