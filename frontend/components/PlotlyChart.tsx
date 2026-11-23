'use client';

import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';

interface PlotlyChartProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  className?: string;
  style?: React.CSSProperties;
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({
  data,
  layout = {},
  config = {},
  className = '',
  style = {}
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    const defaultLayout: Partial<Plotly.Layout> = {
      autosize: true,
      margin: { l: 50, r: 30, t: 30, b: 40 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { family: 'Plus Jakarta Sans, sans-serif', color: '#334155', size: 12 },
      xaxis: { gridcolor: '#e2e8f0', zerolinecolor: '#cbd5e1' },
      yaxis: { gridcolor: '#e2e8f0', zerolinecolor: '#cbd5e1' },
      ...layout,
    };

    const defaultConfig: Partial<Plotly.Config> = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      ...config,
    };

    Plotly.newPlot(element, data, defaultLayout, defaultConfig);

    const handleResize = () => {
      if (element) {
        Plotly.Plots.resize(element);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (element) {
        Plotly.purge(element);
      }
    };
  }, [data, layout, config]);

  return <div ref={containerRef} className={`w-full h-full min-h-[300px] ${className}`} style={style} />;
};
