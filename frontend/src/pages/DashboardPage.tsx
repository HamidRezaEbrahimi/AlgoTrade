import React, { useEffect } from 'react';
import { BalanceCard } from '../components/dashboard/BalanceCard';
import { ActivePositions } from '../components/dashboard/ActivePositions';
import { OpportunityList } from '../components/scanner/OpportunityList';
import { useOrderStore } from '../stores/useOrderStore';
import { useMarketStore } from '../stores/useMarketStore';

export const DashboardPage: React.FC = () => {
  const { fetchBalance, fetchPositions } = useOrderStore();
  const { fetchOpportunities, fetchCandles, fetchSymbols } = useMarketStore();

  useEffect(() => {
    fetchBalance();
    fetchPositions();
    fetchOpportunities();
    fetchCandles();
    fetchSymbols();
  }, [fetchBalance, fetchPositions, fetchOpportunities, fetchCandles, fetchSymbols]);

  return (
    <div className="space-y-6">
      <BalanceCard />
      <ActivePositions />
      <div className="mt-8">
        <OpportunityList />
      </div>
    </div>
  );
};
