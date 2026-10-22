import React, { useEffect } from 'react';
import { OpportunityList } from '../components/scanner/OpportunityList';
import { useMarketStore } from '../stores/useMarketStore';

export const ScannerPage: React.FC = () => {
  const { fetchOpportunities } = useMarketStore();

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  return (
    <div className="space-y-6">
      <OpportunityList />
    </div>
  );
};
