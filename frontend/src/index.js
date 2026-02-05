import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import { initPerformanceOptimizations, reportWebVitals } from "@/utils/performance";

// Initialize performance optimizations
initPerformanceOptimizations();

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Report Web Vitals for monitoring
if (process.env.NODE_ENV === 'development') {
  reportWebVitals((metric) => {
    console.log(`📊 ${metric.name}:`, metric.value);
  });
}
