import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AlertOctagon, ShieldAlert } from 'lucide-react';
import axios from 'axios';
import { useAppStore } from '../../stores/useAppStore';

export const KillSwitchButton: React.FC = () => {
  const { t } = useTranslation('Common');
  const { isKillSwitchModalOpen, openKillSwitchModal, closeKillSwitchModal } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any | null>(null);

  const handleTrigger = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/system/kill-switch');
      setReport(res.data);
    } catch (e: any) {
      setReport({
        success: false,
        message_fa: 'ارتباط با سرور برقرار نشد. وضعیت صرافی را مستقیماً بررسی کنید.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={openKillSwitchModal}
        className="btn btn-danger text-xs font-bold uppercase tracking-wider py-1.5 px-3 shadow-lg shadow-red-950/50"
      >
        <AlertOctagon size={16} />
        <span>{t('kill_switch')}</span>
      </button>

      {isKillSwitchModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="glass-panel p-6 max-w-md w-full border-red-500/30">
            <div className="flex items-center gap-3 text-red-400 mb-4">
              <ShieldAlert size={28} />
              <h3 className="text-lg font-bold">هشدار قطع اضطراری (Kill-Switch)</h3>
            </div>

            {!report ? (
              <>
                <p className="text-sm text-slate-300 mb-6 leading-relaxed">
                  با فشردن این دکمه، بلافاصله:
                  <br />• تمام سفارشات فعال در کلیه صرافی‌ها لغو می‌شوند.
                  <br />• تمامی پوزیشن‌های باز متوقف و بسته خواهند شد.
                  <br />• موتور استراتژی تا زمان بازنشانی دستی متوقف می‌شود.
                </p>

                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={closeKillSwitchModal}
                    className="btn btn-outline text-sm"
                  >
                    {t('cancel')}
                  </button>
                  <button
                    type="button"
                    onClick={handleTrigger}
                    disabled={loading}
                    className="btn btn-danger text-sm font-bold"
                  >
                    {loading ? t('loading') : t('confirm')}
                  </button>
                </div>
              </>
            ) : (
              <div>
                <div className="p-3 bg-red-950/40 border border-red-500/20 rounded-md text-sm text-red-200 mb-4">
                  {report.message_fa}
                </div>
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setReport(null);
                      closeKillSwitchModal();
                    }}
                    className="btn btn-primary text-sm"
                  >
                    {t('confirm')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
