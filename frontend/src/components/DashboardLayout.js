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
  CreditCard,
  DollarSign,
  Upload,
  ChevronDown
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';
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
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleForceLogout = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (window.confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
      forceLogout();
    }
  };

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  const menuItems = [
    { path: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" />, label: t('dashboard'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/orders', icon: <Package className="w-5 h-5" />, label: t('orders'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/orders/import', icon: <Upload className="w-5 h-5" />, label: 'Import Masse', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/products', icon: <ShoppingCart className="w-5 h-5" />, label: t('products'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/customers', icon: <Users className="w-5 h-5" />, label: t('customers'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/users/drivers', icon: <Truck className="w-5 h-5" />, label: 'Chauffeurs', roles: ['admin'] },
    { path: '/dashboard/finance/cod', icon: <DollarSign className="w-5 h-5" />, label: 'Finance COD', roles: ['admin'] },
    { path: '/dashboard/subscriptions', icon: <CreditCard className="w-5 h-5" />, label: 'Abonnements', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/whatsapp', icon: <MessageCircle className="w-5 h-5" />, label: 'WhatsApp', roles: ['admin'] },
    { path: '/dashboard/settings/ai', icon: <Bot className="w-5 h-5" />, label: 'Configuration IA', roles: ['admin'] },
    { path: '/dashboard/settings/integrations', icon: <Truck className="w-5 h-5" />, label: 'Intégrations', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/settings/pricing', icon: <Settings className="w-5 h-5" />, label: 'Tarifs Livraison', roles: ['admin'] },
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
            {/* Theme Toggle */}
            <ThemeToggle />
            
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

            {/* User Profile Menu */}
            <div className="relative">
              <button 
                onClick={() => setProfileMenuOpen(!profileMenuOpen)} 
                className="flex items-center gap-2 p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                {user?.picture ? (
                  <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center text-white font-bold">
                    {user?.name?.[0]?.toUpperCase()}
                  </div>
                )}
                <div className="hidden md:block text-left">
                  <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                  <p className="text-xs text-gray-500">{t(user?.role)}</p>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${profileMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {profileMenuOpen && (
                <>
                  {/* Backdrop to close menu when clicking outside */}
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setProfileMenuOpen(false)}
                  />
                  
                  {/* Dropdown Menu */}
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                    <div className="px-4 py-3 border-b border-gray-100">
                      <p className="text-sm font-bold text-gray-900">{user?.name}</p>
                      <p className="text-xs text-gray-500">{user?.email}</p>
                      <p className="text-xs text-gray-400 mt-1">{t(user?.role)}</p>
                    </div>
                    
                    <button 
                      onClick={handleForceLogout}
                      className="w-full text-left px-4 py-3 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors font-medium"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Déconnexion</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside
        className={`fixed top-16 left-0 bottom-0 w-64 bg-white border-r border-gray-200 transition-transform duration-300 z-30 flex flex-col ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
        data-testid="sidebar"
      >
        <nav className="p-4 space-y-2 flex-1 overflow-y-auto">
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
        </nav>

        {/* LOGOUT BUTTON - HARDCODED INLINE */}
        <div className="mt-auto border-t border-gray-200 dark:border-gray-700 p-4">
          <button
            onClick={(e) => {
              e.preventDefault();
              // 1. Nettoyage Brutal (Directement ici, pas d'import)
              localStorage.clear();
              sessionStorage.clear();
              
              // 2. Destruction Cookies
              document.cookie.split(";").forEach((c) => {
                document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
              });

              // 3. Redirection Force (Pas de React Router)
              window.location.href = '/login'; 
            }}
            className="flex w-full items-center rounded-lg bg-red-600 px-4 py-3 text-sm font-bold text-white shadow-md hover:bg-red-700 transition-colors"
            data-testid="logout-button"
          >
            {/* Icône SVG Hardcodée pour éviter les erreurs d'import d'icônes */}
            <svg xmlns="http://www.w3.org/2000/svg" className="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            DÉCONNEXION
          </button>
        </div>
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