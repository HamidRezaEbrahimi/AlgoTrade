import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, X, Server, Bot, Cpu } from 'lucide-react';
import { ProviderMeta } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSave: (payload: any) => Promise<void>;
  editIntegration?: any;
}

export const AddIntegrationModal: React.FC<Props> = ({ isOpen, onClose, onSave, editIntegration }) => {
  const { t } = useTranslation(['Settings', 'Common']);

  const [selectedType, setSelectedType] = useState<'exchange' | 'bot_telegram' | 'bot_bale' | 'ai_agent'>(
    editIntegration ? editIntegration.type : 'exchange'
  );
  const [selectedProvider, setSelectedProvider] = useState<string>(
    editIntegration ? editIntegration.provider : 'faraz'
  );
  const [name, setName] = useState<string>(editIntegration ? editIntegration.name : '');
  const [apiKey, setApiKey] = useState<string>(editIntegration?.config?.api_key || '');
  const [apiSecret, setApiSecret] = useState<string>(editIntegration?.config?.api_secret || '');
  const [token, setToken] = useState<string>(editIntegration?.config?.token || '');
  const [chatId, setChatId] = useState<string>(editIntegration?.config?.chat_id || '');

  // Faraz specific configuration
  const [farazDomain, setFarazDomain] = useState<string>(editIntegration?.config?.faraz_domain || 'https://ir4.faraz.io');
  const [farazCookie, setFarazCookie] = useState<string>(
    editIntegration?.config?.faraz_cookie ||
    '_ga=GA1.1.993785333.1779340663; farazSession=s%3AjVEnviZTQ4yqHPh2Kcv_UzGR6WyE28fB.CaXUlUVZLWA7QcBYXWFlHKrXFlZavYC0GJYubENez%2B4; x-access-token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2NjcxNTkxNTE5MDM2NmJkMTJkMDcyNjYiLCJjcmVkaXQiOjE4MDAyNDMwMjY4ODQsImFjdGl2ZSI6dHJ1ZSwicm9sZSI6ImN1c3RvbWVyIiwibGFzdFVwZGF0ZVRpbWUiOjE3ODc2NDYxNTY5MzYsImlhdCI6MTc4NzY0NjE1NiwiZXhwIjoxNzg3NjUzMzU2fQ.WhC_d0Wi697z011kyPTOJBKZ1wsaLpuFZsgNEpMF89c'
  );
  const [farazToken, setFarazToken] = useState<string>(
    editIntegration?.config?.faraz_token ||
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2NjcxNTkxNTE5MDM2NmJkMTJkMDcyNjYiLCJjcmVkaXQiOjE4MDAyNDMwMjY4ODQsImFjdGl2ZSI6dHJ1ZSwicm9sZSI6ImN1c3RvbWVyIiwibGFzdFVwZGF0ZVRpbWUiOjE3ODc2NDYxNTY5MzYsImlhdCI6MTc4NzY0NjE1NiwiZXhwIjoxNzg3NjUzMzU2fQ.WhC_d0Wi697z011kyPTOJBKZ1wsaLpuFZsgNEpMF89c'
  );
  const [farazCountback, setFarazCountback] = useState<number>(editIntegration?.config?.faraz_countback || 4800);
  const [farazAdjustType, setFarazAdjustType] = useState<string>(editIntegration?.config?.faraz_adjust_type || '2');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const availableProviders: ProviderMeta[] = [
    { id: 'faraz', name: 'Faraz / فراز (دیتا فید طلا و فارکس)', type: 'exchange', badge: 'طلا، فارکس و کریپتو', desc: 'دیتا فید فراز با سشن کوکی' },
    { id: 'wallex', name: 'Wallex (والکس)', type: 'exchange', badge: 'کریپتو و تومانی', desc: 'صرافی والکس' },
    { id: 'nobitex', name: 'Nobitex (نوبیتکس)', type: 'exchange', badge: 'کریپتو و تومانی', desc: 'صرافی نوبیتکس' },
    { id: 'telegram', name: 'Telegram Bot', type: 'bot_telegram', badge: 'پیام‌رسان', desc: 'ربات تلگرام' },
    { id: 'bale', name: 'Bale Messenger', type: 'bot_bale', badge: 'پیام‌رسان ایرانی', desc: 'ربات بله' },
    { id: 'gemini', name: 'Gemini 2.5 Flash', type: 'ai_agent', badge: 'هوش مصنوعی', desc: 'مدل گوگل جمینای' },
    { id: 'deepseek', name: 'DeepSeek R1', type: 'ai_agent', badge: 'استدلال عمیق', desc: 'مدل دیپ‌سیک' },
  ];

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const config: Record<string, any> = {};
      if (selectedProvider === 'faraz') {
        config.faraz_domain = farazDomain;
        config.faraz_cookie = farazCookie;
        config.faraz_token = farazToken;
        config.faraz_countback = farazCountback;
        config.faraz_adjust_type = farazAdjustType;
      } else {
        if (apiKey) config.api_key = apiKey;
        if (apiSecret) config.api_secret = apiSecret;
        if (token) config.token = token;
        if (chatId) config.chat_id = chatId;
      }

      const payload: any = {
        name: name || (selectedProvider === 'faraz' ? 'فراز (Faraz Feed)' : selectedProvider),
        provider: selectedProvider,
        type: selectedType,
        config,
        is_active: editIntegration ? editIntegration.is_active : true,
      };
      
      if (editIntegration && editIntegration.id) {
        payload.id = editIntegration.id;
      }
      
      await onSave(payload);
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm select-none">
      <div className="glass-panel w-full max-w-lg p-6 space-y-4 border border-white/20 shadow-2xl bg-[#0c1220] max-h-[90vh] overflow-y-auto custom-scrollbar">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Plus size={16} className="text-cyan-400" />
            <span>{editIntegration ? 'ویرایش تنظیمات صرافی' : 'تنظیمات صرافی و اتصال دیتا'}</span>
          </h3>
          <button type="button" onClick={onClose} className="text-slate-400 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          {/* Category Tabs */}
          <div>
            <label className="block text-slate-300 font-bold mb-1.5">{t('modal.service_type')}</label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => {
                  setSelectedType('exchange');
                  setSelectedProvider('faraz');
                }}
                className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-[11px] ${
                  selectedType === 'exchange'
                    ? 'border-cyan-500 bg-cyan-500/20 text-white font-bold'
                    : 'border-white/10 bg-slate-900/60 text-slate-400'
                }`}
              >
                <Server size={16} />
                <span>{t('modal.type_exchange')}</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedType('bot_telegram');
                  setSelectedProvider('telegram');
                }}
                className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-[11px] ${
                  selectedType.startsWith('bot_')
                    ? 'border-cyan-500 bg-cyan-500/20 text-white font-bold'
                    : 'border-white/10 bg-slate-900/60 text-slate-400'
                }`}
              >
                <Bot size={16} />
                <span>{t('modal.type_bot')}</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedType('ai_agent');
                  setSelectedProvider('gemini');
                }}
                className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-[11px] ${
                  selectedType === 'ai_agent'
                    ? 'border-cyan-500 bg-cyan-500/20 text-white font-bold'
                    : 'border-white/10 bg-slate-900/60 text-slate-400'
                }`}
              >
                <Cpu size={16} />
                <span>{t('modal.type_ai')}</span>
              </button>
            </div>
          </div>

          {/* Provider Select */}
          <div>
            <label className="block text-slate-300 font-bold mb-1">{t('modal.provider_label')}</label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="w-full bg-slate-950 border border-white/10 rounded-xl p-2.5 text-white focus:outline-none focus:border-cyan-400"
            >
              {availableProviders
                .filter((p) => {
                  if (selectedType === 'exchange') return p.type === 'exchange';
                  if (selectedType.startsWith('bot_')) return p.type.startsWith('bot_');
                  return p.type === 'ai_agent';
                })
                .map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
            </select>
          </div>

          {/* Name Field */}
          <div>
            <label className="block text-slate-300 font-bold mb-1">{t('modal.name_label')}</label>
            <input
              type="text"
              value={name}
              placeholder={t('modal.name_placeholder')}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-950 border border-white/10 rounded-xl p-2.5 text-white focus:outline-none focus:border-cyan-400"
            />
          </div>

          {/* Faraz Specific Configuration Fields */}
          {selectedProvider === 'faraz' && (
            <div className="space-y-3 p-3.5 rounded-xl bg-slate-950/80 border border-cyan-500/20">
              <div className="flex items-center justify-between">
                <span className="text-cyan-300 font-bold text-[11px]">پارامترهای سشن و API فراز</span>
                <span className="text-[10px] text-slate-400">TradingView API</span>
              </div>

              <div>
                <label className="block text-slate-300 mb-1 text-[11px]">آدرس دامنه فراز (Domain):</label>
                <input
                  type="text"
                  value={farazDomain}
                  onChange={(e) => setFarazDomain(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 font-mono text-white text-xs focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 text-[11px]">سشن کوکی مرورگر (Cookie کپی شده از Network):</label>
                <textarea
                  rows={4}
                  value={farazCookie}
                  placeholder="_ga=...; farazSession=...; x-access-token=..."
                  onChange={(e) => {
                    const val = e.target.value;
                    setFarazCookie(val);
                    const jwtMatch = val.match(/x-access-token=([^;]+)/);
                    if (jwtMatch && jwtMatch[1]) {
                      setFarazToken(jwtMatch[1].trim());
                    }
                  }}
                  className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 font-mono text-white text-[10.5px] focus:border-cyan-400"
                />
                <span className="text-[10px] text-slate-500 mt-0.5 block">
                  کوکی استخراج‌شده از مرورگر شامل farazSession و x-access-token
                </span>
              </div>

              {farazToken && (
                <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[10px] text-emerald-300 font-bold">توکن دسترسی (JWT) با موفقیت شناسایی شد</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-300 mb-1 text-[11px]">عمق تاریخچه (Countback):</label>
                  <input
                    type="number"
                    value={farazCountback}
                    onChange={(e) => setFarazCountback(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 font-mono text-white text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 mb-1 text-[11px]">نوع تعدیل (Adjust Type):</label>
                  <input
                    type="text"
                    value={farazAdjustType}
                    onChange={(e) => setFarazAdjustType(e.target.value)}
                    className="w-full bg-slate-900 border border-white/10 rounded-lg p-2 font-mono text-white text-xs"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Standard Exchange Fields (Wallex, Nobitex) */}
          {selectedType === 'exchange' && selectedProvider !== 'faraz' && (
            <div className="space-y-3">
              <div>
                <label className="block text-slate-300 mb-1">{t('modal.api_key')}</label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-slate-950 border border-white/10 rounded-lg p-2 font-mono text-white"
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">{t('modal.api_secret')}</label>
                <input
                  type="password"
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  className="w-full bg-slate-950 border border-white/10 rounded-lg p-2 font-mono text-white"
                />
              </div>
            </div>
          )}

          {/* Bot Fields */}
          {selectedType.startsWith('bot_') && (
            <div className="space-y-3">
              <div>
                <label className="block text-slate-300 mb-1">{t('modal.token')}</label>
                <input
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="w-full bg-slate-950 border border-white/10 rounded-lg p-2 font-mono text-white"
                />
              </div>
              <div>
                <label className="block text-slate-300 mb-1">{t('modal.chat_id')}</label>
                <input
                  type="text"
                  value={chatId}
                  onChange={(e) => setChatId(e.target.value)}
                  className="w-full bg-slate-950 border border-white/10 rounded-lg p-2 font-mono text-white"
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-xs btn-ghost text-slate-400 hover:text-white"
            >
              {t('Common:actions.cancel')}
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-xs btn-primary gap-1 font-bold shadow-md shadow-cyan-500/20"
            >
              {isSubmitting ? (
                <div className="w-3 h-3 rounded-full border-2 border-white/20 border-t-white animate-spin" />
              ) : editIntegration ? (
                <>
                  <Server size={12} />
                  <span>بروزرسانی</span>
                </>
              ) : (
                <>
                  <Plus size={12} />
                  <span>ذخیره و فعال‌سازی اتصال</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
