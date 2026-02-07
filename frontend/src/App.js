import React, { useEffect, lazy, Suspense } from 'react';
import ErrorBoundary from '@/components/ErrorBoundary';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';
import { Toaster } from 'sonner';
import { AnimatePresence } from 'framer-motion';

// Loading spinner
const PageLoader = () => (
  <div className="min-h-screen flex flex-col items-center justify-center bg-background">
    <div className="aurora-spinner" />
    <p className="mt-4 text-muted-foreground text-sm font-medium animate-pulse">Chargement...</p>
  </div>
);

// Eager-loaded public pages
import LandingPageModern from '@/pages/LandingPageModernV2';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import TrackingPage from '@/pages/TrackingPage';
import DriverLogin from '@/pages/DriverLogin';
import DriverLayout from '@/components/DriverLayout';
import DashboardLayout from '@/components/DashboardLayout';

// Lazy-loaded dashboard pages
const AdminDashboardModern = lazy(() => import('@/pages/AdminDashboardModern'));
const OrdersPageAdvanced = lazy(() => import('@/pages/OrdersPageAdvanced'));
const ProductsPage = lazy(() => import('@/pages/ProductsPage'));
const CustomersPageAdvanced = lazy(() => import('@/pages/CustomersPageAdvanced'));
const WhatsAppDashboard = lazy(() => import('@/pages/WhatsAppDashboard'));
const SubscriptionsPage = lazy(() => import('@/pages/SubscriptionsPage'));
const CarriersIntegrationPage = lazy(() => import('@/pages/CarriersIntegrationPage'));
const FinancialCODPage = lazy(() => import('@/pages/FinancialCODPage'));
const PricingManagementPage = lazy(() => import('@/pages/PricingManagementPage'));
const BulkImportPage = lazy(() => import('@/pages/BulkImportPage'));
const DriverTasks = lazy(() => import('@/pages/DriverTasks'));
const DriversManagementPage = lazy(() => import('@/pages/DriversManagementPage'));
const AIConfigPage = lazy(() => import('@/pages/AIConfigPage'));
const ReturnsPage = lazy(() => import('@/pages/ReturnsPage'));
const WarehousePage = lazy(() => import('@/pages/WarehousePage'));
const AIBrainPage = lazy(() => import('@/pages/AIBrainPage'));

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
};

const LP = (C) => (
  <Suspense fallback={<PageLoader />}><C /></Suspense>
);

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPageModern />} />
      <Route path="/tracking" element={<TrackingPage />} />
      <Route path="/tracking/:tracking_id" element={<TrackingPage />} />
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

      {/* Protected dashboard */}
      <Route path="/dashboard" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        <Route index element={LP(AdminDashboardModern)} />
        <Route path="orders" element={LP(OrdersPageAdvanced)} />
        <Route path="products" element={LP(ProductsPage)} />
        <Route path="customers" element={LP(CustomersPageAdvanced)} />
        <Route path="whatsapp" element={LP(WhatsAppDashboard)} />
        <Route path="subscriptions" element={LP(SubscriptionsPage)} />
        <Route path="settings/integrations" element={LP(CarriersIntegrationPage)} />
        <Route path="settings/pricing" element={LP(PricingManagementPage)} />
        <Route path="finance/cod" element={LP(FinancialCODPage)} />
        <Route path="orders/import" element={LP(BulkImportPage)} />
        <Route path="users/drivers" element={LP(DriversManagementPage)} />
        <Route path="settings/ai" element={LP(AIConfigPage)} />
        <Route path="returns" element={LP(ReturnsPage)} />
        <Route path="warehouse" element={LP(WarehousePage)} />
        <Route path="ai-brain" element={LP(AIBrainPage)} />
      </Route>

      {/* Driver routes */}
      <Route path="/driver/login" element={<DriverLogin />} />
      <Route path="/driver" element={<DriverLayout />}>
        <Route path="tasks" element={LP(DriverTasks)} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  useEffect(() => {
    const updateDirection = () => {
      const lang = localStorage.getItem('language') || 'fr';
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
      document.documentElement.lang = lang;
    };
    updateDirection();
    window.addEventListener('storage', updateDirection);
    return () => window.removeEventListener('storage', updateDirection);
  }, []);

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <I18nextProvider i18n={i18n}>
          <AuthProvider>
            <BrowserRouter>
              <AppRoutes />
              <Toaster position="top-right" richColors />
            </BrowserRouter>
          </AuthProvider>
        </I18nextProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
