/**
 * Performance Monitoring & Optimization Utilities
 * Tracks Core Web Vitals and provides optimization tips
 */

// Report Web Vitals to console (can be extended to analytics)
export const reportWebVitals = (onPerfEntry) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ onCLS, onFID, onFCP, onLCP, onTTFB }) => {
      onCLS(onPerfEntry);
      onFID(onPerfEntry);
      onFCP(onPerfEntry);
      onLCP(onPerfEntry);
      onTTFB(onPerfEntry);
    }).catch(() => {
      // Fallback if web-vitals not available
      console.log('⚠️ Web Vitals library not available');
    });
  }
};

// Performance marks for custom metrics
export const markPerformance = (name) => {
  if ('performance' in window && performance.mark) {
    performance.mark(name);
  }
};

export const measurePerformance = (name, startMark, endMark) => {
  if ('performance' in window && performance.measure) {
    try {
      performance.measure(name, startMark, endMark);
      const measure = performance.getEntriesByName(name)[0];
      console.log(`⚡ ${name}: ${measure.duration.toFixed(2)}ms`);
      return measure.duration;
    } catch (error) {
      console.warn(`Failed to measure ${name}:`, error);
    }
  }
  return null;
};

// Log initial load performance
export const logInitialLoadPerformance = () => {
  if ('performance' in window) {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const perfData = performance.getEntriesByType('navigation')[0];
        
        if (perfData) {
          console.group('🚀 Performance Metrics');
          console.log(`DNS Lookup: ${(perfData.domainLookupEnd - perfData.domainLookupStart).toFixed(2)}ms`);
          console.log(`TCP Connection: ${(perfData.connectEnd - perfData.connectStart).toFixed(2)}ms`);
          console.log(`Request Time: ${(perfData.responseStart - perfData.requestStart).toFixed(2)}ms`);
          console.log(`Response Time: ${(perfData.responseEnd - perfData.responseStart).toFixed(2)}ms`);
          console.log(`DOM Processing: ${(perfData.domComplete - perfData.domLoading).toFixed(2)}ms`);
          console.log(`🎯 Total Load Time: ${(perfData.loadEventEnd - perfData.fetchStart).toFixed(2)}ms`);
          console.groupEnd();
          
          // Check if under 800ms target
          const totalTime = perfData.loadEventEnd - perfData.fetchStart;
          if (totalTime < 800) {
            console.log('✅ PERFORMANCE TARGET ACHIEVED: <0.8s');
          } else {
            console.warn(`⚠️ Performance: ${totalTime.toFixed(0)}ms (Target: <800ms)`);
          }
        }
      }, 0);
    });
  }
};

// Preload critical resources
export const preloadCriticalResources = () => {
  // Preload critical fonts
  const fonts = [
    '/fonts/inter-var.woff2',
    // Add your critical fonts here
  ];
  
  fonts.forEach(font => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'font';
    link.type = 'font/woff2';
    link.href = font;
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
};

// Optimize images with lazy loading
export const setupImageLazyLoading = () => {
  if ('IntersectionObserver' in window) {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          observer.unobserve(img);
        }
      });
    });
    
    images.forEach(img => imageObserver.observe(img));
  }
};

// Initialize all optimizations
export const initPerformanceOptimizations = () => {
  logInitialLoadPerformance();
  
  // Setup lazy loading for images
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupImageLazyLoading);
  } else {
    setupImageLazyLoading();
  }
};
