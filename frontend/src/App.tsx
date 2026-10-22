import { Header } from './components/shared/Header';
import { Sidebar } from './components/shared/Sidebar';
import { useAppStore } from './stores/useAppStore';

import { DashboardPage } from './pages/DashboardPage';
import { TradingPage } from './pages/trading';
import { AIAgentPage } from './pages/ai_copilot';
import { ScannerPage } from './pages/ScannerPage';
import { OrdersPage } from './pages/OrdersPage';
import { StrategyBuilderPage } from './pages/strategy_builder';
import { AIOptimizerPage } from './pages/ai_optimizer';
import { BacktestPage } from './pages/BacktestPage';
import { SettingsPage } from './pages/settings';

export function App() {
  const { activePage } = useAppStore();

  const renderActivePage = () => {
    switch (activePage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'trading':
        return <TradingPage />;
      case 'ai_copilot':
        return <AIAgentPage />;
      case 'scanner':
        return <ScannerPage />;
      case 'orders':
        return <OrdersPage />;
      case 'strategy_builder':
        return <StrategyBuilderPage />;
      case 'ai_optimizer':
        return <AIOptimizerPage />;
      case 'backtest':
        return <BacktestPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-slate-950">
      <Header />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6 transition-all duration-300">
          <div className="w-full max-w-[1780px] mx-auto space-y-6">{renderActivePage()}</div>
        </main>
      </div>
    </div>
  );
}

export default App;
