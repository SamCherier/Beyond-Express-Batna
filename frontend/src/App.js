import React, { useEffect, lazy, Suspense } from 'react';
import ErrorBoundary from '@/components/ErrorBoundary';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';
import { Toaster } from 'sonner';

// Loading Component
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-gray-100">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
  </div>
);

// Eager loading for public pages (fast initial load)
import LandingPageModern from '@/pages/LandingPageModern';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardLayout from '@/components/DashboardLayout';

// Lazy loading for dashboard pages (code splitting)
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
const DriversManagementPage = lazy(() => import('@/pages/DriversManagementPage'));

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Public Route Component (redirect if already logged in)
const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPageModern />} />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />

      {/* Protected Routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={
          <Suspense fallback={<PageLoader />}>
            <AdminDashboardModern />
          </Suspense>
        } />
        <Route path="orders" element={
          <Suspense fallback={<PageLoader />}>
            <OrdersPageAdvanced />
          </Suspense>
        } />
        <Route path="products" element={
          <Suspense fallback={<PageLoader />}>
            <ProductsPage />
          </Suspense>
        } />
        <Route path="customers" element={
          <Suspense fallback={<PageLoader />}>
            <CustomersPageAdvanced />
          </Suspense>
        } />
        <Route path="whatsapp" element={
          <Suspense fallback={<PageLoader />}>
            <WhatsAppDashboard />
          </Suspense>
        } />
        <Route path="subscriptions" element={
          <Suspense fallback={<PageLoader />}>
            <SubscriptionsPage />
          </Suspense>
        } />
        <Route path="settings/integrations" element={
          <Suspense fallback={<PageLoader />}>
            <CarriersIntegrationPage />
          </Suspense>
        } />
        <Route path="settings/pricing" element={
          <Suspense fallback={<PageLoader />}>
            <PricingManagementPage />
          </Suspense>
        } />
        <Route path="finance/cod" element={
          <Suspense fallback={<PageLoader />}>
            <FinancialCODPage />
          </Suspense>
        } />
        <Route path="orders/import" element={
          <Suspense fallback={<PageLoader />}>
            <BulkImportPage />
          </Suspense>
        } />
        <Route path="users/drivers" element={
          <Suspense fallback={<PageLoader />}>
            <DriversManagementPage />
          </Suspense>
        } />
        <Route path="delivery-partners" element={<div className="p-8 text-center">Delivery Partners Page - Coming Soon</div>} />
        <Route path="invoices" element={<div className="p-8 text-center">Invoices Page - Coming Soon</div>} />
        <Route path="support" element={<div className="p-8 text-center">Support Page - Coming Soon</div>} />
        <Route path="settings" element={<div className="p-8 text-center">Settings Page - Coming Soon</div>} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  useEffect(() => {
    // Set document direction based on language
    const updateDirection = () => {
      const lang = localStorage.getItem('language') || 'fr';
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
      document.documentElement.lang = lang;
    };

    updateDirection();
    
    // Listen for language changes
    window.addEventListener('storage', updateDirection);
    
    return () => window.removeEventListener('storage', updateDirection);
  }, []);

  return (
    <ErrorBoundary>
      <I18nextProvider i18n={i18n}>
        <AuthProvider>
          <BrowserRouter>
            <AppRoutes />
            <Toaster position="top-right" richColors />
          </BrowserRouter>
        </AuthProvider>
      </I18nextProvider>
    </ErrorBoundary>
  );
}

export default App;
