import React from 'react';
import { useTranslation } from 'react-i18next';
import { Server, Bot, Cpu, RefreshCw, Trash2, CheckCircle2, AlertTriangle, AlertCircle } from 'lucide-react';
import { IntegrationItem } from '../types';

interface Props {
  integrations: IntegrationItem[];
  selectedCategory: string;
  setSelectedCategory: (cat: string) => void;
  testingId: string | null;
  testFeedback?: { id: string; status: 'success' | 'error'; message: string } | null;
  onTestConnection: (id: string) => void;
  onToggleActive: (id: string, current: boolean) => void;
  onDeleteIntegration: (id: string) => void;
  onEditIntegration: (item: IntegrationItem) => void;
}

export const IntegrationsTab: React.FC<Props> = ({
  integrations,
  selectedCategory,
  setSelectedCategory,
  testingId,
  testFeedback,
  onTestConnection,
  onToggleActive,
  onDeleteIntegration,
  onEditIntegration,
}) => {
  const { t } = useTranslation(['Settings', 'Common']);

  const filteredIntegrations = integrations.filter((item) => {
    if (selectedCategory === 'all') return true;
    if (selectedCategory === 'exchange') return item.type === 'exchange';
    if (selectedCategory === 'bot') return item.type.startsWith('bot_');
    if (selectedCategory === 'ai') return item.type === 'ai_agent';
    return true;
  });

  const getProviderIcon = (type: string) => {
    if (type === 'exchange') return <Server size={18} className="text-cyan-400" />;
    if (type.startsWith('bot_')) return <Bot size={18} className="text-emerald-400" />;
    return <Cpu size={18} className="text-purple-400" />;
  };

  return (
    <div className="space-y-4">
      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <button
          type="button"
          onClick={() => setSelectedCategory('all')}
          className={`btn btn-xs rounded-lg ${
            selectedCategory === 'all' ? 'btn-primary' : 'btn-ghost bg-slate-900/60 text-slate-400'
          }`}
        >
          {t('filters.all')}
        </button>
        <button
          type="button"
          onClick={() => setSelectedCategory('exchange')}
          className={`btn btn-xs rounded-lg ${
            selectedCategory === 'exchange' ? 'btn-primary' : 'btn-ghost bg-slate-900/60 text-slate-400'
          }`}
        >
          {t('filters.exchange')}
        </button>
        <button
          type="button"
          onClick={() => setSelectedCategory('bot')}
          className={`btn btn-xs rounded-lg ${
            selectedCategory === 'bot' ? 'btn-primary' : 'btn-ghost bg-slate-900/60 text-slate-400'
          }`}
        >
          {t('filters.bot')}
        </button>
        <button
          type="button"
          onClick={() => setSelectedCategory('ai')}
          className={`btn btn-xs rounded-lg ${
            selectedCategory === 'ai' ? 'btn-primary' : 'btn-ghost bg-slate-900/60 text-slate-400'
          }`}
        >
          {t('filters.ai')}
        </button>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredIntegrations.map((item) => (
          <div
            key={item.id}
            className="glass-panel p-5 space-y-4 flex flex-col justify-between hover:border-cyan-500/30 transition-all"
          >
            <div>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-slate-900/80 border border-white/10 flex items-center justify-center">
                    {getProviderIcon(item.type)}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white">{item.name}</h3>
                    <span className="text-[10px] text-slate-400 font-mono uppercase">{item.provider}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  {item.status === 'connected' ? (
                    <span className="badge badge-success text-[9px] gap-1">
                      <CheckCircle2 size={10} />
                      {t('Common:status.online')}
                    </span>
                  ) : (
                    <span className="badge badge-warning text-[9px] gap-1">
                      <AlertTriangle size={10} />
                      {t('Common:status.offline')}
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-3 p-2.5 rounded-lg bg-slate-900/60 border border-white/5 space-y-1 text-[11px] font-mono text-slate-300">
                {item.config.api_key && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">API Key:</span>
                    <span>{item.config.api_key.substring(0, 6)}...</span>
                  </div>
                )}
                {item.config.chat_id && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Chat ID:</span>
                    <span>{item.config.chat_id}</span>
                  </div>
                )}
              </div>

              {testFeedback && testFeedback.id === item.id && (
                <div
                  className={`mt-2 p-2 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all animate-fade-in ${
                    testFeedback.status === 'success'
                      ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                  }`}
                >
                  {testFeedback.status === 'success' ? (
                    <CheckCircle2 size={12} className="text-emerald-400 shrink-0" />
                  ) : (
                    <AlertCircle size={12} className="text-rose-400 shrink-0" />
                  )}
                  <span>{testFeedback.message}</span>
                </div>
              )}
            </div>

            <div className="pt-2 border-t border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => onTestConnection(item.id)}
                  disabled={testingId === item.id}
                  className="btn btn-xs btn-ghost border border-white/10 text-cyan-400 hover:bg-cyan-500/10 gap-1"
                >
                  <RefreshCw size={11} className={testingId === item.id ? 'animate-spin' : ''} />
                  <span>{t('Common:actions.test_connection')}</span>
                </button>
                <button
                  type="button"
                  onClick={() => onEditIntegration(item)}
                  className="btn btn-xs btn-ghost border border-white/10 text-emerald-400 hover:bg-emerald-500/10 gap-1"
                >
                  <span className="text-[10px]">ویرایش</span>
                </button>
                <button
                  type="button"
                  onClick={() => onDeleteIntegration(item.id)}
                  className="btn btn-xs btn-ghost text-red-400 hover:bg-red-500/10"
                >
                  <Trash2 size={11} />
                </button>
              </div>

              <input
                type="checkbox"
                checked={item.is_active}
                onChange={() => onToggleActive(item.id, item.is_active)}
                className="toggle toggle-xs toggle-primary"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
