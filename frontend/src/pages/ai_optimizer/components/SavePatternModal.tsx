import React, { useState } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { BookmarkPlus, X, CheckCircle2 } from 'lucide-react';
import { DiscoveredPattern, CustomPatternItem } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  initialPattern?: DiscoveredPattern | null;
  onSaved: (pattern: CustomPatternItem) => void;
}

export const SavePatternModal: React.FC<Props> = ({
  isOpen,
  onClose,
  initialPattern,
  onSaved,
}) => {
  const { t } = useTranslation('AIOptimizer');

  const [nameFa, setNameFa] = useState<string>(initialPattern?.name_fa || '');
  const nameEn = initialPattern?.name_en || '';
  const [patternKey, setPatternKey] = useState<string>(initialPattern?.pattern_id || `pat_${Date.now()}`);
  const [category, setCategory] = useState<string>(initialPattern?.category || 'smc');
  const [descriptionFa, setDescriptionFa] = useState<string>(initialPattern?.description_fa || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: CustomPatternItem = {
      id: patternKey,
      name_fa: nameFa || 'الگوی اختصاصی',
      name_en: nameEn || patternKey,
      category: category,
      timeframe: initialPattern?.timeframe || '1h',
      win_rate_estimate: initialPattern?.win_rate || 70.0,
      profit_factor_estimate: initialPattern?.profit_factor || 2.2,
      description_fa: descriptionFa,
      rules: initialPattern?.rules || {},
      tags: ['custom', category],
      created_at: new Date().toISOString().replace('T', ' ').substring(0, 19),
    };

    try {
      const res = await axios.post('/api/ai-optimizer/custom-patterns', payload);
      onSaved(res.data || payload);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'خطا در ذخیره‌سازی الگو');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="glass-panel w-full max-w-md p-5 rounded-2xl border border-cyan-500/30 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <BookmarkPlus size={18} className="text-cyan-400" />
            <h3 className="text-sm font-bold text-white">{t('save_modal.title')}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {error && (
          <div className="alert alert-error text-xs py-2 px-3">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3 text-xs">
          <div>
            <label className="block text-slate-300 mb-1 font-medium">{t('save_modal.name_label')}</label>
            <input
              type="text"
              required
              value={nameFa}
              onChange={(e) => setNameFa(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-300 mb-1 font-medium">{t('save_modal.key_label')}</label>
              <input
                type="text"
                dir="ltr"
                required
                value={patternKey}
                onChange={(e) => setPatternKey(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-white font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 mb-1 font-medium">{t('save_modal.category_label')}</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-white"
              >
                <option value="smc">اسمارت‌مانی (SMC)</option>
                <option value="geometric">هندسی / امواج</option>
                <option value="candlestick">کندل‌استیک</option>
                <option value="custom">سفارشی ترکیبی</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-300 mb-1 font-medium">{t('save_modal.desc_label')}</label>
            <textarea
              rows={3}
              value={descriptionFa}
              onChange={(e) => setDescriptionFa(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2 text-white resize-none focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-sm btn-ghost border border-white/10 text-slate-300"
            >
              {t('save_modal.btn_cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-sm btn-primary gap-1.5 shadow-lg shadow-cyan-500/20 font-bold"
            >
              <CheckCircle2 size={14} />
              <span>{loading ? 'در حال ذخیره...' : t('save_modal.btn_confirm')}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
