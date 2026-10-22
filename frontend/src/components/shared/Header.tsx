import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, ShieldCheck, Wifi, WifiOff } from 'lucide-react';
import { useAppStore } from '../../stores/useAppStore';
import { useMarketStore } from '../../stores/useMarketStore';
import { useOrderStore } from '../../stores/useOrderStore';
import { KillSwitchButton } from './KillSwitchButton';

export const Header: React.FC = () => {
  const { t, i18n } = useTranslation('Common');
  const { currentLanguage, setLanguage } = useAppStore();
  const [isConnected, setIsConnected] = useState(false);

  const handleLanguageToggle = () => {
    const nextLang = currentLanguage === 'fa' ? 'en' : 'fa';
    setLanguage(nextLang);
    i18n.changeLanguage(nextLang);
    document.documentElement.dir = nextLang === 'fa' ? 'rtl' : 'ltr';
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let pingInterval: any = null;
    let reconnectTimeout: any = null;

    const connectWs = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        pingInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 15000);
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const parsed = JSON.parse(event.data);
          useMarketStore.getState().handleWsMessage(parsed);
          useOrderStore.getState().handleWsMessage(parsed);
        } catch {
          // ignore non-json messages
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        clearInterval(pingInterval);
        reconnectTimeout = setTimeout(connectWs, 3000);
      };

      ws.onerror = () => {
        ws?.close();
      };
    };

    connectWs();

    return () => {
      clearInterval(pingInterval);
      clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, []);

  return (
    <header className="h-16 border-b border-white/10 glass-panel rounded-none px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-md shadow-cyan-500/20">
          AT
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
            AlgoTrade
            <span className="badge badge-accent text-[10px] py-0.5">v0.2.0</span>
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Trading Mode Badge */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
          <ShieldCheck size={14} />
          <span>{t('status.paper_trading')}</span>
        </div>

        {/* WebSocket Status */}
        <div
          className={`flex items-center gap-1.5 text-xs ${
            isConnected ? 'text-emerald-400' : 'text-amber-400'
          }`}
        >
          {isConnected ? (
            <>
              <Wifi size={14} className="text-emerald-400" />
              <span className="hidden sm:inline">{t('status.online')}</span>
            </>
          ) : (
            <>
              <WifiOff size={14} className="text-amber-400 animate-pulse" />
              <span className="hidden sm:inline">{t('actions.loading')}</span>
            </>
          )}
        </div>

        {/* Language Switcher */}
        <button
          type="button"
          onClick={handleLanguageToggle}
          className="btn btn-outline py-1 px-2.5 text-xs flex items-center gap-1.5 font-mono border-white/15 hover:border-cyan-400"
        >
          <Globe size={14} className="text-cyan-400" />
          <span>{currentLanguage.toUpperCase()}</span>
        </button>

        {/* Kill Switch */}
        <KillSwitchButton />
      </div>
    </header>
  );
};
