import React from 'react';
import { useTranslation } from 'react-i18next';
import { Bot, User, RefreshCw, CheckCircle2 } from 'lucide-react';
import { ChatMessage } from '../types';

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

export const ChatFeed: React.FC<Props> = ({ messages, loading, messagesEndRef }) => {
  const { t } = useTranslation('AICopilot');

  return (
    <div className="glass-panel p-5 space-y-4 flex flex-col h-[480px]">
      <div className="flex items-center gap-2 border-b border-white/10 pb-2.5">
        <Bot size={18} className="text-cyan-400" />
        <h3 className="text-sm font-bold text-white">{t('chat.header_title')}</h3>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${
              msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-xl shrink-0 flex items-center justify-center ${
                msg.role === 'user'
                  ? 'bg-cyan-500 text-slate-950 font-bold'
                  : 'bg-slate-900 border border-white/10 text-cyan-400'
              }`}
            >
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>

            <div
              className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed space-y-2.5 ${
                msg.role === 'user'
                  ? 'bg-cyan-500/20 text-white rounded-tr-none border border-cyan-500/30'
                  : 'bg-slate-900/90 text-slate-200 rounded-tl-none border border-white/10 shadow-lg'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* Action Payload Box */}
              {msg.actionPayload && (
                <div className="p-3 rounded-xl bg-slate-950/80 border border-emerald-500/30 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="badge badge-success text-[9px] gap-1">
                      <CheckCircle2 size={10} />
                      {t('chat.trade_setup_badge')}
                    </span>
                    <span className="font-mono text-cyan-400 font-bold">
                      {msg.actionPayload.symbol}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
                    <div className="bg-slate-900 p-1.5 rounded">
                      <span className="text-slate-500 block">SL:</span>
                      <span className="text-red-400 font-bold">{msg.actionPayload.sl}</span>
                    </div>
                    <div className="bg-slate-900 p-1.5 rounded">
                      <span className="text-slate-500 block">TP1 (1.5R):</span>
                      <span className="text-emerald-400 font-bold">{msg.actionPayload.tp1}</span>
                    </div>
                    <div className="bg-slate-900 p-1.5 rounded">
                      <span className="text-slate-500 block">TP2 (2.5R):</span>
                      <span className="text-cyan-400 font-bold">{msg.actionPayload.tp2}</span>
                    </div>
                  </div>
                </div>
              )}

              <span className="text-[9px] text-slate-500 block text-left font-mono">
                {msg.timestamp}
              </span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate-400 p-3 bg-slate-900/40 rounded-xl w-fit">
            <RefreshCw size={14} className="animate-spin text-cyan-400" />
            <span>{t('chat.loading_reasoning')}</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};
