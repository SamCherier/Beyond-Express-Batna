import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import useFeatureAccess from '@/hooks/useFeatureAccess';
import FeatureLock from '@/components/FeatureLock';
import BeyondExpressLogo from '@/components/BeyondExpressLogo';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard, Package, ShoppingCart, Users, Truck,
  FileText, Settings, LogOut, MessageCircle, Menu, X,
  Bot, CreditCard, DollarSign, Upload, ChevronDown,
  RotateCcw, Warehouse, Home, ScanLine, ClipboardList, User
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import AIAssistant from '@/components/AIAssistant';
import { AnimatePresence, motion } from 'framer-motion';

const DashboardLayout = () => {
  const { user, logout } = useAuth();
  const { checkAccess, getUpgradeMessage } = useFeatureAccess();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [showLockModal, setShowLockModal] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [isTablet, setIsTablet] = useState(window.innerWidth >= 768 && window.innerWidth <= 1024);

  useEffect(() => {
    const onResize = () => {
      const w = window.innerWidth;
      setIsMobile(w < 768);
      setIsTablet(w >= 768 && w <= 1024);
      if (w >= 1025) setSidebarOpen(true);
      if (w < 768) setSidebarOpen(false);
    };
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Close sidebar on nav in mobile
  useEffect(() => {
    if (isMobile) setSidebarOpen(false);
  }, [location.pathname, isMobile]);

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  const handleForceLogout = () => {
    localStorage.clear();
    sessionStorage.clear();
    document.cookie.split(';').forEach((c) => {
      document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=' + new Date().toUTCString() + ';path=/');
    });
    window.location.href = '/login';
  };

  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: t('dashboard'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/orders', icon: Package, label: t('orders'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/orders/import', icon: Upload, label: 'Import Masse', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/products', icon: ShoppingCart, label: t('products'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/customers', icon: Users, label: t('customers'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/users/drivers', icon: Truck, label: 'Chauffeurs', roles: ['admin'] },
    { path: '/dashboard/finance/cod', icon: DollarSign, label: 'Finance COD', roles: ['admin'] },
    { path: '/dashboard/returns', icon: RotateCcw, label: 'Retours RMA', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/warehouse', icon: Warehouse, label: 'Entrepôt', roles: ['admin'] },
    { path: '/dashboard/subscriptions', icon: CreditCard, label: 'Abonnements', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/whatsapp', icon: MessageCircle, label: 'WhatsApp', roles: ['admin'] },
    { path: '/dashboard/settings/ai', icon: Bot, label: 'Configuration IA', roles: ['admin'] },
    { path: '/dashboard/settings/integrations', icon: Truck, label: 'Intégrations', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/settings/pricing', icon: Settings, label: 'Tarifs Livraison', roles: ['admin'] },
  ];

  const bottomNavItems = [
    { path: '/dashboard', icon: Home, label: 'Accueil' },
    { path: '/dashboard/orders', icon: Package, label: 'Colis' },
    { path: '/dashboard/returns', icon: RotateCcw, label: 'Retours' },
    { path: '/dashboard/settings/integrations', icon: Settings, label: 'Config' },
  ];

  const filteredMenuItems = menuItems.filter(item => item.roles.includes(user?.role));

  const isActive = (path) => {
    if (path === '/dashboard') return location.pathname === '/dashboard';
    return location.pathname.startsWith(path);
  };

  const sidebarWidth = isTablet && !sidebarOpen ? 72 : 256;
  const showSidebar = !isMobile;

  return (
    <div className="min-h-screen bg-background" data-testid="dashboard-layout">
      {/* ===== TOP HEADER ===== */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-card border-b border-border z-40 flex items-center px-4" data-testid="top-header">
        <div className="flex items-center gap-3 flex-1">
          {!isMobile && (
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} className="shrink-0" data-testid="sidebar-toggle">
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          )}
          {isMobile && (
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)} data-testid="mobile-menu-btn">
              <Menu className="w-5 h-5" />
            </Button>
          )}
          <BeyondExpressLogo size="sm" />
          <span className="text-base font-bold text-foreground hidden sm:block">Beyond Express</span>
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <div className="hidden md:flex gap-1">
            {['fr', 'ar', 'en'].map(lng => (
              <button key={lng} onClick={() => changeLanguage(lng)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors ${i18n.language === lng ? 'bg-[var(--aurora-primary)] text-white' : 'bg-muted text-muted-foreground hover:bg-accent'}`}
                data-testid={`lang-${lng}`}
              >{lng.toUpperCase()}</button>
            ))}
          </div>

          {/* Profile */}
          <div className="relative z-50">
            <button onClick={(e) => { e.stopPropagation(); setProfileMenuOpen(!profileMenuOpen); }}
              className="flex items-center gap-2 p-1.5 hover:bg-accent rounded-lg transition-colors"
              data-testid="profile-menu-button"
            >
              <div className="w-8 h-8 rounded-full bg-[var(--aurora-primary)] flex items-center justify-center text-white font-bold text-sm">
                {user?.name?.[0]?.toUpperCase()}
              </div>
              <div className="hidden lg:block text-left">
                <p className="text-sm font-medium text-foreground leading-tight">{user?.name}</p>
                <p className="text-[10px] text-muted-foreground">{t(user?.role)}</p>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 text-muted-foreground transition-transform ${profileMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {profileMenuOpen && (
              <>
                <div className="fixed inset-0 z-[60]" onClick={() => setProfileMenuOpen(false)} />
                <div className="absolute right-0 mt-1 w-52 bg-card rounded-xl shadow-xl border border-border z-[70] overflow-hidden">
                  <div className="px-4 py-3 border-b border-border">
                    <p className="text-sm font-bold text-foreground">{user?.name}</p>
                    <p className="text-xs text-muted-foreground">{user?.email}</p>
                  </div>
                  <button onClick={handleForceLogout}
                    className="w-full text-left px-4 py-3 text-sm text-destructive hover:bg-destructive/10 flex items-center gap-2 font-medium"
                    data-testid="logout-dropdown-btn"
                  >
                    <LogOut className="w-4 h-4" /> Déconnexion
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ===== MOBILE OVERLAY ===== */}
      <AnimatePresence>
        {isMobile && sidebarOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 z-30" onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* ===== SIDEBAR ===== */}
      <aside
        className={`fixed top-14 bottom-0 bg-card border-r border-border z-30 flex flex-col transition-all duration-300 ${
          isMobile
            ? `w-64 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`
            : showSidebar ? '' : 'hidden'
        }`}
        style={!isMobile ? { width: sidebarWidth } : undefined}
        data-testid="sidebar"
      >
        <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {filteredMenuItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            const collapsed = isTablet && !sidebarOpen;
            return (
              <Link key={item.path} to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm font-medium ${
                  active
                    ? 'bg-[var(--aurora-primary)] text-white shadow-sm'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                } ${collapsed ? 'justify-center px-2' : ''}`}
                title={collapsed ? item.label : undefined}
                data-testid={`nav-${item.path.replace(/\//g, '-')}`}
              >
                <Icon className="w-[18px] h-[18px] shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-border p-2">
          <button onClick={handleForceLogout}
            className={`flex w-full items-center gap-3 rounded-lg bg-destructive px-3 py-2.5 text-sm font-bold text-destructive-foreground hover:bg-destructive/90 transition-colors ${isTablet && !sidebarOpen ? 'justify-center px-2' : ''}`}
            data-testid="logout-button"
          >
            <LogOut className="w-[18px] h-[18px] shrink-0" />
            {!(isTablet && !sidebarOpen) && <span>DÉCONNEXION</span>}
          </button>
        </div>
      </aside>

      {/* ===== MAIN CONTENT ===== */}
      <main
        className="pt-14 transition-all duration-300"
        style={{ paddingLeft: isMobile ? 0 : sidebarWidth, paddingBottom: isMobile ? 72 : 0 }}
      >
        <div className="p-4 md:p-6">
          <AnimatePresence mode="wait">
            <motion.div key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* ===== MOBILE BOTTOM NAV ===== */}
      {isMobile && (
        <nav className="bottom-nav" data-testid="bottom-nav">
          {bottomNavItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link key={item.path} to={item.path}
                className={`bottom-nav-item ${active ? 'active' : ''}`}
                data-testid={`bottom-nav-${item.label.toLowerCase()}`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      )}

      {/* ===== AI ASSISTANT ===== */}
      <button
        onClick={() => checkAccess('ai_content_generator') ? setAiOpen(true) : setShowLockModal(true)}
        className={`fixed z-50 w-12 h-12 text-white rounded-full shadow-lg flex items-center justify-center transition-all ${
          isMobile ? 'bottom-[76px] right-4' : 'bottom-6 right-6'
        } ${checkAccess('ai_content_generator') ? 'bg-[var(--aurora-primary)] hover:bg-[var(--aurora-primary)]/90' : 'bg-muted-foreground/50 cursor-not-allowed'}`}
        data-testid="ai-assistant-button"
      >
        <Bot className="w-5 h-5" />
      </button>

      {aiOpen && checkAccess('ai_content_generator') && <AIAssistant onClose={() => setAiOpen(false)} />}
      {showLockModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowLockModal(false)}>
          <div onClick={(e) => e.stopPropagation()}>
            <FeatureLock feature="ai_content_generator" message={getUpgradeMessage('ai_content_generator')} requiredPlan="pro" variant="card" />
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardLayout;
