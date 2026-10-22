export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  actionPayload?: {
    symbol?: string;
    action?: string;
    score?: number;
    tp1?: number;
    tp2?: number;
    sl?: number;
  };
}

export interface Persona {
  id: string;
  name: string;
  roleTitle: string;
  description: string;
  icon: 'smc' | 'risk' | 'scalp';
}
