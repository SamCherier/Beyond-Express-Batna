import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Route Prefetcher - Preload critical routes on idle
 * Improves perceived performance by loading pages before user clicks
 */

// Define prefetch strategies
const PREFETCH_STRATEGIES = {
  // After login, prefetch dashboard
  '/login': [
    () => import('@/pages/AdminDashboardModern'),
    () => import('@/pages/OrdersPageAdvanced')
  ],
  
  // On dashboard, prefetch orders (most accessed)
  '/dashboard': [
    () => import('@/pages/OrdersPageAdvanced'),
    () => import('@/pages/CustomersPageAdvanced')
  ],
  
  // On orders page, prefetch related pages
  '/dashboard/orders': [
    () => import('@/pages/BulkImportPage'),
    () => import('@/pages/CarriersIntegrationPage')
  ]
};

export const useRoutePrefetch = () => {
  const location = useLocation();
  
  useEffect(() => {
    // Get prefetch list for current route
    const prefetchList = PREFETCH_STRATEGIES[location.pathname];
    
    if (!prefetchList || prefetchList.length === 0) return;
    
    // Use requestIdleCallback for non-critical prefetching
    if ('requestIdleCallback' in window) {
      const idleCallback = window.requestIdleCallback(() => {
        prefetchList.forEach((importFunc, index) => {
          // Stagger prefetch to avoid blocking
          setTimeout(() => {
            importFunc().catch(err => {
              console.warn(`Prefetch failed for route ${index}:`, err);
            });
          }, index * 300);
        });
      });
      
      return () => {
        if (idleCallback) {
          window.cancelIdleCallback(idleCallback);
        }
      };
    } else {
      // Fallback for browsers without requestIdleCallback
      const timeout = setTimeout(() => {
        prefetchList.forEach((importFunc) => {
          importFunc().catch(err => {
            console.warn('Prefetch failed:', err);
          });
        });
      }, 1000);
      
      return () => clearTimeout(timeout);
    }
  }, [location.pathname]);
};

export default useRoutePrefetch;
