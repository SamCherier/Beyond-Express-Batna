import React, { useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n';
import { Toaster } from 'sonner';

// Pages
import LandingPageModern from '@/pages/LandingPageModern';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardLayout from '@/components/DashboardLayout';
import AdminDashboardModern from '@/pages/AdminDashboardModern';
import OrdersPageAdvanced from '@/pages/OrdersPageAdvanced';
import ProductsPage from '@/pages/ProductsPage';
import CustomersPageAdvanced from '@/pages/CustomersPageAdvanced';
import WhatsAppDashboard from '@/pages/WhatsAppDashboard';
import SubscriptionsPage from '@/pages/SubscriptionsPage';
import CarriersIntegrationPage from '@/pages/CarriersIntegrationPage';

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
        <Route index element={<AdminDashboardModern />} />
        <Route path="orders" element={<OrdersPageAdvanced />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="customers" element={<CustomersPageAdvanced />} />
        <Route path="whatsapp" element={<WhatsAppDashboard />} />
        <Route path="subscriptions" element={<SubscriptionsPage />} />
        <Route path="settings/integrations" element={<CarriersIntegrationPage />} />
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
    <I18nextProvider i18n={i18n}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      </AuthProvider>
    </I18nextProvider>
  );
}

export default App;
