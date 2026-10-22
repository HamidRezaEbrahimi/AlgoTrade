import React, { useEffect, useRef } from 'react';
import { createChart, IChartApi } from 'lightweight-charts';

interface Props {
  data?: { time: number; value: number }[];
}

export const RSIPanel: React.FC<Props> = ({ data }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 140,
      layout: {
        background: { color: 'transparent' },
        textColor: '#64748b',
        fontFamily: 'Inter, sans-serif',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.02)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.08)',
      },
    });

    const lineSeries = chart.addLineSeries({
      color: '#06b6d4',
      lineWidth: 2,
    });

    // 70 Overbought level
    lineSeries.createPriceLine({
      price: 70,
      color: 'rgba(239, 68, 68, 0.6)',
      lineWidth: 1,
      lineStyle: 2,
      title: '70',
    });

    // 30 Oversold level
    lineSeries.createPriceLine({
      price: 30,
      color: 'rgba(16, 185, 129, 0.6)',
      lineWidth: 1,
      lineStyle: 2,
      title: '30',
    });

    chartRef.current = chart;

    if (data && data.length > 0) {
      lineSeries.setData(data as any);
    } else {
      const now = Math.floor(Date.now() / 1000);
      const sample = [];
      for (let i = 60; i >= 0; i--) {
        const val = 50 + Math.sin(i / 4) * 18;
        sample.push({ time: (now - i * 3600) as any, value: val });
      }
      lineSeries.setData(sample);
    }

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <div className="mt-2">
      <div className="text-xs text-slate-400 font-semibold px-2 py-1 flex items-center justify-between border-t border-white/5">
        <span>RSI (14)</span>
        <span className="text-cyan-400 font-mono">54.2</span>
      </div>
      <div ref={containerRef} className="w-full" />
    </div>
  );
};
