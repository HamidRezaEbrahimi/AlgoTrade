export interface IntegrationItem {
  id: string;
  name: string;
  provider: string;
  type: 'exchange' | 'bot_telegram' | 'bot_bale' | 'bot_discord' | 'ai_agent';
  config: Record<string, any>;
  is_active: boolean;
  status: 'connected' | 'error' | 'untested' | 'pending';
  last_ping?: string;
}

export interface ProviderMeta {
  id: string;
  name: string;
  type: 'exchange' | 'bot_telegram' | 'bot_bale' | 'bot_discord' | 'ai_agent';
  badge: string;
  desc: string;
}
