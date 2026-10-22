import React from 'react';
import { BacktestRunner } from '../components/backtest/BacktestRunner';

export const BacktestPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <BacktestRunner />
    </div>
  );
};
