import React, { useState } from 'react';
import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import useFeatureAccess from '@/hooks/useFeatureAccess';
import FeatureLock from '@/components/FeatureLock';
import BeyondExpressLogo from '@/components/BeyondExpressLogo';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Users,
  Truck,
  FileText,
  Settings,
  LogOut,
  MessageSquare,
  MessageCircle,
  Menu,
  X,
  Bot,
  CreditCard
} from 'lucide-react';
import AIAssistant from '@/components/AIAssistant';

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const { checkAccess, getUpgradeMessage } = useFeatureAccess();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [aiOpen, setAiOpen] = useState(false);
  const [showLockModal, setShowLockModal] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  const menuItems = [
    { path: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" />, label: t('dashboard'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/orders', icon: <Package className="w-5 h-5" />, label: t('orders'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/products', icon: <ShoppingCart className="w-5 h-5" />, label: t('products'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/customers', icon: <Users className="w-5 h-5" />, label: t('customers'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/subscriptions', icon: <CreditCard className="w-5 h-5" />, label: 'Abonnements', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/whatsapp', icon: <MessageCircle className="w-5 h-5" />, label: 'WhatsApp', roles: ['admin'] },
    { path: '/dashboard/delivery-partners', icon: <Truck className="w-5 h-5" />, label: t('deliveryPartners'), roles: ['admin'] },
    { path: '/dashboard/invoices', icon: <FileText className="w-5 h-5" />, label: t('invoices'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/support', icon: <MessageSquare className="w-5 h-5" />, label: t('support'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/settings', icon: <Settings className="w-5 h-5" />, label: t('settings'), roles: ['admin', 'ecommerce', 'delivery'] },
  ];

  const filteredMenuItems = menuItems.filter(item => item.roles.includes(user?.role));

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100" data-testid="dashboard-layout">
      {/* Top Header */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-40">
        <div className="h-full px-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden"
              data-testid="sidebar-toggle"
            >
              {sidebarOpen ? <X /> : <Menu />}
            </Button>
            
            <div className="flex items-center gap-3">
              <BeyondExpressLogo size="sm" />
              <span className="text-xl font-bold text-gray-900 hidden sm:block" style={{ fontFamily: 'Brockmann, sans-serif' }}>
                Beyond Express
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Language Switcher */}
            <div className="hidden md:flex gap-2">
              <button
                onClick={() => changeLanguage('fr')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'fr' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                FR
              </button>
              <button
                onClick={() => changeLanguage('ar')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'ar' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                AR
              </button>
              <button
                onClick={() => changeLanguage('en')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'en' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                EN
              </button>
            </div>

            {/* User Info */}
            <div className="flex items-center gap-3">
              {user?.picture ? (
                <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center text-white font-bold">
                  {user?.name?.[0]?.toUpperCase()}
                </div>
              )}
              <div className="hidden sm:block">
                <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                <p className="text-xs text-gray-500">{t(user?.role)}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={`fixed top-16 left-0 bottom-0 w-64 bg-white border-r border-gray-200 transition-transform duration-300 z-30 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
        data-testid="sidebar"
      >
        <nav className="p-4 space-y-2">
          {filteredMenuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-red-500 text-white shadow-md'
                    : 'text-gray-700 hover:bg-red-50 hover:text-red-600'
                }`}
                data-testid={`nav-${item.path}`}
              >
                {item.icon}
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-red-50 hover:text-red-600 w-full transition-all"
            data-testid="logout-button"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">{t('logout')}</span>
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main
        className={`pt-16 transition-all duration-300 ${
          sidebarOpen ? 'lg:pl-64' : 'pl-0'
        }`}
      >
        <div className="p-6">
          <Outlet />
        </div>
      </main>

      {/* AI Assistant Button */}
      <button
        onClick={() => {
          if (checkAccess('ai_content_generator')) {
            setAiOpen(true);
          } else {
            setShowLockModal(true);
          }
        }}
        className={`fixed bottom-6 right-6 w-14 h-14 text-white rounded-full shadow-2xl flex items-center justify-center transition-all z-50 ${
          checkAccess('ai_content_generator')
            ? 'bg-red-500 hover:bg-red-600 hover:scale-110'
            : 'bg-gray-400 cursor-not-allowed opacity-60'
        }`}
        data-testid="ai-assistant-button"
        title={checkAccess('ai_content_generator') 
          ? 'Ouvrir l\'Assistant IA' 
          : 'Plan PRO requis pour l\'Assistant IA'
        }
      >
        <Bot className="w-6 h-6" />
        {!checkAccess('ai_content_generator') && (
          <div className="absolute -top-1 -right-1 w-5 h-5 bg-orange-500 rounded-full flex items-center justify-center">
            <span className="text-white text-xs font-bold">🔒</span>
          </div>
        )}
      </button>

      {/* AI Assistant Modal */}
      {aiOpen && checkAccess('ai_content_generator') && <AIAssistant onClose={() => setAiOpen(false)} />}

      {/* Feature Lock Modal */}
      {showLockModal && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowLockModal(false)}
        >
          <div onClick={(e) => e.stopPropagation()}>
            <FeatureLock
              feature="ai_content_generator"
              message={getUpgradeMessage('ai_content_generator')}
              requiredPlan="pro"
              variant="card"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardLayout;