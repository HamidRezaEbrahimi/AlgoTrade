import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Farsi translations
import faCommon from './fa/common.json';
import faDashboard from './fa/dashboard.json';
import faStrategies from './fa/strategies.json';
import faStrategyBuilder from './fa/strategy_builder.json';
import faSettings from './fa/settings.json';
import faTrading from './fa/trading.json';
import faAICopilot from './fa/ai_copilot.json';
import faOrders from './fa/orders.json';
import faRisk from './fa/risk.json';
import faScanner from './fa/scanner.json';
import faBacktest from './fa/backtest.json';
import faAIOptimizer from './fa/ai_optimizer.json';

// English translations
import enCommon from './en/common.json';
import enDashboard from './en/dashboard.json';
import enStrategies from './en/strategies.json';
import enStrategyBuilder from './en/strategy_builder.json';
import enSettings from './en/settings.json';
import enTrading from './en/trading.json';
import enAICopilot from './en/ai_copilot.json';
import enOrders from './en/orders.json';
import enRisk from './en/risk.json';
import enScanner from './en/scanner.json';
import enBacktest from './en/backtest.json';
import enAIOptimizer from './en/ai_optimizer.json';

i18n.use(initReactI18next).init({
  resources: {
    fa: {
      Common: faCommon,
      Dashboard: faDashboard,
      Strategies: faStrategies,
      StrategyBuilder: faStrategyBuilder,
      Settings: faSettings,
      Trading: faTrading,
      AICopilot: faAICopilot,
      Orders: faOrders,
      Risk: faRisk,
      Scanner: faScanner,
      Backtest: faBacktest,
      AIOptimizer: faAIOptimizer,
    },
    en: {
      Common: enCommon,
      Dashboard: enDashboard,
      Strategies: enStrategies,
      StrategyBuilder: enStrategyBuilder,
      Settings: enSettings,
      Trading: enTrading,
      AICopilot: enAICopilot,
      Orders: enOrders,
      Risk: enRisk,
      Scanner: enScanner,
      Backtest: enBacktest,
      AIOptimizer: enAIOptimizer,
    },
  },
  lng: 'fa',
  fallbackLng: 'fa',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
