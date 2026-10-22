import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
  currentPrice: number;
}

export const OrderEntryModal: React.FC<Props> = ({
  isOpen,
  onClose,
  symbol,
  currentPrice,
}) => {
  const { t } = useTranslation(['Trading', 'Common']);
  const [direction, setDirection] = useState<'BUY' | 'SELL'>('BUY');
  const [amount, setAmount] = useState<number>(100);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [success, setSuccess] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 1500);
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-md p-6 space-y-4 border border-white/20 shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <h3 className="text-sm font-bold text-white">{t('order_modal.title')}</h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-white">
            <X size={18} />
          </button>
        </div>

        {success ? (
          <div className="p-6 text-center space-y-2">
            <CheckCircle2 size={36} className="text-emerald-400 mx-auto" />
            <p className="text-sm font-bold text-white">{t('order_modal.order_success')}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 font-mono">
              <span className="text-slate-400">{t('order_modal.symbol_label')} {symbol}</span>
              <span className="text-cyan-400 font-bold">{currentPrice.toLocaleString()} USDT</span>
            </div>

            <div>
              <label className="block text-slate-300 mb-1.5">{t('order_modal.direction_label')}</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setDirection('BUY')}
                  className={`py-2 rounded-lg font-bold ${
                    direction === 'BUY'
                      ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20'
                      : 'bg-slate-900 text-slate-400'
                  }`}
                >
                  {t('order_modal.dir_buy')}
                </button>
                <button
                  type="button"
                  onClick={() => setDirection('SELL')}
                  className={`py-2 rounded-lg font-bold ${
                    direction === 'SELL'
                      ? 'bg-red-500 text-white shadow-md shadow-red-500/20'
                      : 'bg-slate-900 text-slate-400'
                  }`}
                >
                  {t('order_modal.dir_sell')}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-slate-300 mb-1">{t('order_modal.amount_label')}</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 font-mono text-white"
              />
            </div>

            <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/30 flex items-start gap-2 text-amber-300 text-[11px]">
              <ShieldAlert size={16} className="shrink-0 mt-0.5" />
              <span>{t('order_modal.safety_warning')}</span>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <button
                type="button"
                onClick={onClose}
                className="btn btn-xs btn-ghost text-slate-400"
              >
                {t('Common:actions.cancel')}
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn btn-xs btn-primary font-bold"
              >
                {t('order_modal.btn_submit')}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
