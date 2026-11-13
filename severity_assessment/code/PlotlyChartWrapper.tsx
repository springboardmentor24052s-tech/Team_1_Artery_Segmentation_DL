'use client';

import dynamic from 'next/dynamic';
import React from 'react';

const PlotlyDynamic = dynamic(() => import('./PlotlyChart').then((mod) => mod.PlotlyChart), {
  ssr: false,
  loading: () => (
    <div className="w-full h-96 flex items-center justify-center text-slate-400 font-mono text-xs">
      Loading Plotly Visualization Engine...
    </div>
  )
});

export const PlotlyChart = (props: any) => {
  return <PlotlyDynamic {...props} />;
};
