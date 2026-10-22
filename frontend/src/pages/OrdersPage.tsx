import React, { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivePositions } from '../components/dashboard/ActivePositions';
import { useOrderStore } from '../stores/useOrderStore';

export const OrdersPage: React.FC = () => {
  const { t } = useTranslation('Orders');
  const { tradeHistory, fetchPositions, fetchTradeHistory } = useOrderStore();

  useEffect(() => {
    fetchPositions();
    fetchTradeHistory();
  }, [fetchPositions, fetchTradeHistory]);

  return (
    <div className="space-y-6">
      <ActivePositions />

      {/* Trade History */}
      <div className="glass-panel p-5">
        <h3 className="text-base font-bold text-white mb-4">{t('history')}</h3>

        {tradeHistory.length === 0 ? (
          <div className="text-sm text-slate-400 py-8 text-center">
            هنوز هیچ معامله بسته‌شده‌ای ثبت نشده است.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('symbol')}</th>
                  <th>{t('entry_price')}</th>
                  <th>{t('exit_price')}</th>
                  <th>{t('pnl')}</th>
                  <th>{t('risk_reward')}</th>
                  <th>{t('entry_reason')}</th>
                  <th>{t('exit_reason')}</th>
                  <th>{t('time')}</th>
                </tr>
              </thead>
              <tbody>
                {tradeHistory.map((th) => (
                  <tr key={th.id}>
                    <td className="font-bold text-white font-mono">{th.symbol}</td>
                    <td className="font-mono numeric-ltr">${th.entry_price.toLocaleString()}</td>
                    <td className="font-mono numeric-ltr">${th.exit_price.toLocaleString()}</td>
                    <td className="font-mono numeric-ltr text-emerald-400 font-bold">
                      +${th.pnl.toFixed(2)} (+{th.pnl_percent}%)
                    </td>
                    <td className="font-mono numeric-ltr text-cyan-400 font-bold">1:{th.risk_reward_actual}</td>
                    <td className="text-xs text-slate-300">{th.entry_reason}</td>
                    <td className="text-xs text-slate-300">{th.exit_reason}</td>
                    <td className="text-xs text-slate-500 font-mono numeric-ltr">{th.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
