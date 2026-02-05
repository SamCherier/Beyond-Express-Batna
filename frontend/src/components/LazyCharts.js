import React, { lazy, Suspense } from 'react';

// Lazy load Recharts components
const RechartsComponents = lazy(() => import('recharts').then(module => ({
  default: module
})));

// Mini loader for charts
const ChartLoader = ({ height = 300 }) => (
  <div className="flex items-center justify-center animate-pulse" style={{ height }}>
    <div className="text-center">
      <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-red-200 border-t-red-500 mb-2"></div>
      <p className="text-sm text-gray-500">Chargement du graphique...</p>
    </div>
  </div>
);

// Optimized Chart Components with Lazy Loading
export const LazyBarChart = ({ children, ...props }) => (
  <Suspense fallback={<ChartLoader height={props.height || 300} />}>
    {React.createElement(require('recharts').BarChart, props, children)}
  </Suspense>
);

export const LazyLineChart = ({ children, ...props }) => (
  <Suspense fallback={<ChartLoader height={props.height || 300} />}>
    {React.createElement(require('recharts').LineChart, props, children)}
  </Suspense>
);

export const LazyPieChart = ({ children, ...props }) => (
  <Suspense fallback={<ChartLoader height={props.height || 300} />}>
    {React.createElement(require('recharts').PieChart, props, children)}
  </Suspense>
);

// Re-export all Recharts components for convenience
export * from 'recharts';
