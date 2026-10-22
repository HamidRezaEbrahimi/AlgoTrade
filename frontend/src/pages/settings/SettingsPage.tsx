import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Plus, Shield, Layers, Sliders, CheckCircle2, AlertCircle } from 'lucide-react';
import { IntegrationItem } from './types';
import { IntegrationsTab } from './components/IntegrationsTab';
import { AddIntegrationModal } from './components/AddIntegrationModal';
import { SafetyRiskTab } from './components/SafetyRiskTab';
import { TradingRulesTab } from './components/TradingRulesTab';

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation(['Settings', 'Common']);

  const [activeTab, setActiveTab] = useState<'integrations' | 'safety' | 'rules'>('integrations');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [integrations, setIntegrations] = useState<IntegrationItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingIntegration, setEditingIntegration] = useState<IntegrationItem | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);
  const [testFeedback, setTestFeedback] = useState<{
    id: string;
    status: 'success' | 'error';
    message: string;
  } | null>(null);

  const [autoTradingEnabled, setAutoTradingEnabled] = useState<boolean>(false);
  const [maxRiskPerTrade, setMaxRiskPerTrade] = useState<number>(1.0);

  const fetchIntegrations = async () => {
    try {
      const res = await axios.get('/api/integrations');
      setIntegrations(res.data || []);
    } catch {
      // Fallback
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const handleTestConnection = async (id: string) => {
    setTestingId(id);
    setTestFeedback(null);
    try {
      const res = await axios.post(`/api/integrations/${id}/test`);
      if (res.data) {
        setTestFeedback({
          id,
          status: res.data.status === 'success' ? 'success' : 'error',
          message: res.data.message || (res.data.status === 'success' ? 'اتصال با موفقیت برقرار شد.' : 'خطا در برقراری اتصال'),
        });
      }
      fetchIntegrations();
    } catch (err: any) {
      setTestFeedback({
        id,
        status: 'error',
        message: err.response?.data?.detail || err.message || 'خطا در ارتباط با سرور',
      });
    } finally {
      setTestingId(null);
    }
  };

  const handleToggleActive = async (id: string, current: boolean) => {
    try {
      await axios.patch(`/api/integrations/${id}/toggle`, { is_active: !current });
      fetchIntegrations();
    } catch {
      // Fallback
    }
  };

  const handleDeleteIntegration = async (id: string) => {
    try {
      await axios.delete(`/api/integrations/${id}`);
      fetchIntegrations();
    } catch {
      // Fallback
    }
  };

  const handleSaveNewIntegration = async (payload: any) => {
    try {
      if (payload.id) {
        const id = payload.id;
        delete payload.id;
        await axios.put(`/api/integrations/${id}`, payload);
        setSaveSuccessMsg(t('header.saved_success', { defaultValue: 'با موفقیت بروزرسانی شد' }));
      } else {
        await axios.post('/api/integrations', payload);
        setSaveSuccessMsg(t('header.saved_success', { defaultValue: 'با موفقیت ذخیره شد' }));
      }
      setTimeout(() => setSaveSuccessMsg(null), 4000);
      fetchIntegrations();
    } catch (err: any) {
      console.error('Failed to save integration', err);
    }
  };

  const handleSaveRiskParams = () => {
    setSaveSuccessMsg(t('header.saved_success'));
    setTimeout(() => setSaveSuccessMsg(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5">
        <div>
          <h1 className="text-xl font-bold text-white">{t('header.title')}</h1>
          <p className="text-xs text-slate-400 mt-1">{t('header.subtitle')}</p>
        </div>
        {activeTab === 'integrations' && (
          <button
            type="button"
            onClick={() => {
              setEditingIntegration(null);
              setIsModalOpen(true);
            }}
            className="btn btn-sm btn-primary shadow-lg shadow-cyan-500/20 gap-1"
          >
            <Plus size={14} />
            <span>{t('header.btn_add_integration')}</span>
          </button>
        )}
      </div>

      {saveSuccessMsg && (
        <div className="alert alert-success text-xs py-2 px-4 flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {testFeedback && (
        <div
          className={`alert text-xs py-2.5 px-4 flex items-center justify-between gap-2 shadow-lg transition-all animate-fade-in ${
            testFeedback.status === 'success'
              ? 'alert-success border border-emerald-500/30'
              : 'alert-error border border-rose-500/30 bg-rose-950/80 text-rose-200'
          }`}
        >
          <div className="flex items-center gap-2">
            {testFeedback.status === 'success' ? (
              <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle size={16} className="text-rose-400 shrink-0" />
            )}
            <span className="font-bold">{testFeedback.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setTestFeedback(null)}
            className="text-xs opacity-70 hover:opacity-100 font-bold px-2 py-0.5 rounded bg-white/10"
          >
            بستن
          </button>
        </div>
      )}

      {/* Tabs Switcher */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('integrations')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'integrations'
              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Layers size={14} />
          <span>{t('tabs.integrations')}</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('safety')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'safety'
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Shield size={14} />
          <span>{t('tabs.safety')}</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('rules')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'rules'
              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Sliders size={14} />
          <span>{t('tabs.rules')}</span>
        </button>
      </div>

      {/* Active Tab View */}
      {activeTab === 'integrations' && (
        <IntegrationsTab
          integrations={integrations}
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
          testingId={testingId}
          testFeedback={testFeedback}
          onTestConnection={handleTestConnection}
          onToggleActive={handleToggleActive}
          onDeleteIntegration={handleDeleteIntegration}
          onEditIntegration={(item) => {
            setEditingIntegration(item);
            setIsModalOpen(true);
          }}
        />
      )}

      {activeTab === 'safety' && (
        <SafetyRiskTab
          autoTradingEnabled={autoTradingEnabled}
          onToggleAutoTrading={() => setAutoTradingEnabled(!autoTradingEnabled)}
          maxRiskPerTrade={maxRiskPerTrade}
          setMaxRiskPerTrade={setMaxRiskPerTrade}
          onSaveRiskParams={handleSaveRiskParams}
        />
      )}

      {activeTab === 'rules' && <TradingRulesTab />}

      {/* Add Modal */}
      <AddIntegrationModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingIntegration(null);
        }}
        onSave={handleSaveNewIntegration}
        editIntegration={editingIntegration}
      />
    </div>
  );
};
