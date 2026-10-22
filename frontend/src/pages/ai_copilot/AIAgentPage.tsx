import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { Send, Bot, RefreshCw } from 'lucide-react';
import { useMarketStore } from '../../stores/useMarketStore';
import { ChatMessage } from './types';
import { PersonaSelector } from './components/PersonaSelector';
import { ChatFeed } from './components/ChatFeed';
import { QuickPromptBar } from './components/QuickPromptBar';

export const AIAgentPage: React.FC = () => {
  const { t } = useTranslation(['AICopilot', 'Common']);
  const { activeSymbol } = useMarketStore();

  const [selectedPersona, setSelectedPersona] = useState<string>('smc_master');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init_1',
      role: 'assistant',
      content:
        'سلام! من دستیار هوشمند معاملاتی AlgoTrade هستم. با تحلیل چندتایم‌فریمه اسمارت مانی، ساختار چارت، امتیاز ۸ معیاره و اعتبارسنجی ریسک در خدمت شما هستم.',
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage('');
    setLoading(true);

    try {
      const res = await axios.post('/api/ai/chat', {
        message: text,
        symbol: activeSymbol,
        persona: selectedPersona,
      });

      const data = res.data;
      const assistantMsg: ChatMessage = {
        id: `ai_${Date.now()}`,
        role: 'assistant',
        content: data.reply || 'تحلیل با موفقیت انجام شد.',
        timestamp: new Date().toLocaleTimeString(),
        actionPayload: data.trade_setup,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const fallbackMsg: ChatMessage = {
        id: `ai_err_${Date.now()}`,
        role: 'assistant',
        content: t('chat.error_network'),
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Bot size={22} className="text-cyan-400" />
            <span>{t('header.title')}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">{t('header.subtitle')}</p>
        </div>

        <div className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-900/80 border border-white/10 text-xs">
          <span className="text-slate-400">{t('snapshot.active_symbol')}</span>
          <span className="font-bold text-white font-mono">{activeSymbol}</span>
          <span className="badge badge-accent text-[10px]">
            6 / 8
          </span>
        </div>
      </div>

      {/* Persona Selector */}
      <PersonaSelector
        selectedPersona={selectedPersona}
        onSelectPersona={setSelectedPersona}
      />

      {/* Chat Room */}
      <div className="space-y-3">
        <ChatFeed
          messages={messages}
          loading={loading}
          messagesEndRef={messagesEndRef as React.RefObject<HTMLDivElement>}
        />

        {/* Quick Prompts */}
        <QuickPromptBar
          onSelectPrompt={(p) => handleSendMessage(p)}
          selectedSymbol={activeSymbol}
        />

        {/* Input Bar */}
        <div className="glass-panel p-3 flex items-center gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder={t('chat.input_placeholder')}
            className="flex-1 bg-slate-900 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="button"
            onClick={() => handleSendMessage()}
            disabled={loading || !inputMessage.trim()}
            className="btn btn-sm btn-primary rounded-xl px-4 gap-1.5 shadow-lg shadow-cyan-500/20"
          >
            {loading ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
            <span>{t('chat.btn_send')}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
