import React from 'react';
import { useTranslation } from 'react-i18next';
import { useOrderStore } from '../../stores/useOrderStore';

export const ActivePositions: React.FC = () => {
  const { t } = useTranslation('Orders');
  const { positions } = useOrderStore();

  return (
    <div className="glass-panel p-5 mt-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <span>{t('active_positions')}</span>
          <span className="badge badge-accent font-mono">{positions.length} / 4</span>
        </h3>
      </div>

      {positions.length === 0 ? (
        <div className="text-sm text-slate-400 py-8 text-center">
          {t('no_active_positions', { ns: 'Dashboard' })}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('symbol')}</th>
                <th>{t('direction')}</th>
                <th>{t('entry_price')}</th>
                <th>{t('current_stop')}</th>
                <th>{t('size')}</th>
                <th>{t('pnl')}</th>
                <th>{t('status')}</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr key={pos.id}>
                  <td className="font-bold text-white font-mono">{pos.symbol}</td>
                  <td>
                    <span className={`badge ${pos.direction === 'LONG' ? 'badge-bullish' : 'badge-bearish'}`}>
                      {pos.direction}
                    </span>
                  </td>
                  <td className="font-mono numeric-ltr">${pos.entry_price.toLocaleString()}</td>
                  <td className="font-mono numeric-ltr text-amber-400">
                    ${pos.current_stop.toLocaleString()}
                    {pos.trailing_active && <span className="text-[10px] text-cyan-400 ml-1">TR</span>}
                  </td>
                  <td className="font-mono numeric-ltr">{pos.remaining_size}</td>
                  <td className="font-mono numeric-ltr text-emerald-400 font-bold">
                    +${pos.unrealized_pnl.toFixed(2)}
                  </td>
                  <td>
                    <span className="badge badge-accent text-xs">OPEN</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
