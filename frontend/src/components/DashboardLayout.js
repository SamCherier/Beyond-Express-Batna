import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import useFeatureAccess from '@/hooks/useFeatureAccess';
import FeatureLock from '@/components/FeatureLock';
import BeyondExpressLogo from '@/components/BeyondExpressLogo';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard, Package, ShoppingCart, Users, Truck,
  Settings, LogOut, Menu, X, Bot, CreditCard, DollarSign,
  Upload, ChevronDown, RotateCcw, Warehouse, MessageCircle,
  Search, Monitor
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import AIAssistant from '@/components/AIAssistant';
import CommandBar from '@/components/CommandBar';
import { AnimatePresence, motion } from 'framer-motion';

const SIDEBAR_FULL = 264;
const SIDEBAR_ICON = 68;

const DashboardLayout = () => {
  const { user, forceLogout, logoutAllDevices, sessionWarning, setSessionWarning } = useAuth();
  const { checkAccess, getUpgradeMessage } = useFeatureAccess();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [showLockModal, setShowLockModal] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [cmdkOpen, setCmdkOpen] = useState(false);

  const getBreakpoint = useCallback(() => {
    const w = window.innerWidth;
    if (w < 768) return 'mobile';
    if (w < 1024) return 'tablet';
    return 'desktop';
  }, []);

  const [bp, setBp] = useState(getBreakpoint);

  useEffect(() => {
    const onResize = () => setBp(getBreakpoint());
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [getBreakpoint]);

  // Close drawer on nav
  useEffect(() => { setDrawerOpen(false); }, [location.pathname]);

  // Cmd+K shortcut
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdkOpen(o => !o);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  const isMobile = bp === 'mobile';
  const isTablet = bp === 'tablet';
  const sidebarWidth = isMobile ? 0 : (isTablet || sidebarCollapsed) ? SIDEBAR_ICON : SIDEBAR_FULL;
  const isIconOnly = isTablet || sidebarCollapsed;

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: t('dashboard'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/orders', icon: Package, label: t('orders'), roles: ['admin', 'ecommerce', 'delivery'] },
    { path: '/dashboard/orders/import', icon: Upload, label: 'Import', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/products', icon: ShoppingCart, label: t('products'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/customers', icon: Users, label: t('customers'), roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/users/drivers', icon: Truck, label: 'Chauffeurs', roles: ['admin'] },
    { path: '/dashboard/finance/cod', icon: DollarSign, label: 'Finance COD', roles: ['admin'] },
    { path: '/dashboard/returns', icon: RotateCcw, label: 'Retours', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/warehouse', icon: Warehouse, label: 'Entrepôt', roles: ['admin'] },
    { path: '/dashboard/subscriptions', icon: CreditCard, label: 'Abonnements', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/whatsapp', icon: MessageCircle, label: 'WhatsApp', roles: ['admin'] },
    { path: '/dashboard/settings/ai', icon: Bot, label: 'Config IA', roles: ['admin'] },
    { path: '/dashboard/settings/integrations', icon: Truck, label: 'Intégrations', roles: ['admin', 'ecommerce'] },
    { path: '/dashboard/settings/pricing', icon: Settings, label: 'Tarifs', roles: ['admin'] },
  ];

  const filteredNav = navItems.filter(item => item.roles.includes(user?.role));

  const isActive = (path) => {
    if (path === '/dashboard') return location.pathname === '/dashboard';
    return location.pathname.startsWith(path);
  };

  const NavLink = ({ item, mobile }) => {
    const Icon = item.icon;
    const active = isActive(item.path);
    const iconOnly = !mobile && isIconOnly;
    return (
      <Link to={item.path}
        className={`group flex items-center gap-3 rounded-lg transition-all text-sm font-medium
          ${iconOnly ? 'justify-center p-2.5' : 'px-3 py-2.5'}
          ${active
            ? 'bg-[var(--primary-500)] text-white shadow-md shadow-blue-500/20'
            : 'text-muted-foreground hover:bg-accent hover:text-foreground'
          }`}
        title={iconOnly ? item.label : undefined}
        data-testid={`nav-${item.path.replace(/\//g, '-')}`}
      >
        <Icon className={`shrink-0 ${iconOnly ? 'w-5 h-5' : 'w-[18px] h-[18px]'}`} />
        {!iconOnly && <span className="truncate">{item.label}</span>}
      </Link>
    );
  };

  return (
    <div className="min-h-screen bg-background" data-testid="dashboard-layout">
      {/* ═══ Session timeout warning ═══ */}
      <AnimatePresence>
        {sessionWarning && (
          <motion.div initial={{ y: -60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -60, opacity: 0 }}
            className="fixed top-0 left-0 right-0 z-[100] bg-amber-500 text-white px-4 py-2.5 flex items-center justify-center gap-3 text-sm font-semibold"
          >
            <span>Votre session expire dans 2 minutes</span>
            <Button size="sm" variant="secondary" onClick={() => { setSessionWarning(false); }}
              className="bg-white text-amber-600 hover:bg-amber-50 h-7 px-3 text-xs font-bold"
            >Rester connecté</Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ═══ TOP BAR ═══ */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-card/80 backdrop-blur-xl border-b border-border z-40 flex items-center px-4 gap-3"
        style={{ paddingLeft: isMobile ? 16 : sidebarWidth + 16 }} data-testid="top-header"
      >
        {isMobile && (
          <Button variant="ghost" size="icon" onClick={() => setDrawerOpen(true)} data-testid="mobile-menu-btn" className="shrink-0">
            <Menu className="w-5 h-5" />
          </Button>
        )}
        {!isMobile && (
          <Button variant="ghost" size="icon" onClick={() => setSidebarCollapsed(!sidebarCollapsed)} className="shrink-0 hidden lg:flex" data-testid="sidebar-toggle">
            {sidebarCollapsed ? <Menu className="w-5 h-5" /> : <X className="w-5 h-5" />}
          </Button>
        )}

        {/* Cmd+K trigger */}
        <button onClick={() => setCmdkOpen(true)}
          className="no-fx hidden sm:flex items-center gap-2 h-8 px-3 rounded-lg border border-border bg-muted/50 text-muted-foreground text-xs hover:bg-accent transition-colors"
          data-testid="cmdk-trigger"
        >
          <Search className="w-3.5 h-3.5" />
          <span>Rechercher...</span>
          <kbd className="ml-2 pointer-events-none text-[10px] font-mono bg-background px-1.5 py-0.5 rounded border border-border">⌘K</kbd>
        </button>

        <div className="flex-1" />

        <ThemeToggle />

        <div className="hidden md:flex gap-1">
          {['fr', 'ar', 'en'].map(lng => (
            <button key={lng} onClick={() => changeLanguage(lng)}
              className={`no-fx px-2.5 py-1 rounded-md text-xs font-bold transition-colors
                ${i18n.language === lng ? 'bg-[var(--primary-500)] text-white' : 'text-muted-foreground hover:bg-accent'}`}
              data-testid={`lang-${lng}`}
            >{lng.toUpperCase()}</button>
          ))}
        </div>

        {/* Profile */}
        <div className="relative z-50">
          <button onClick={(e) => { e.stopPropagation(); setProfileOpen(!profileOpen); }}
            className="no-fx flex items-center gap-2 p-1.5 hover:bg-accent rounded-lg transition-colors" data-testid="profile-menu-button"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--primary-500)] to-[var(--accent-info)] flex items-center justify-center text-white font-bold text-sm">
              {user?.name?.[0]?.toUpperCase()}
            </div>
            <div className="hidden lg:block text-left">
              <p className="text-sm font-semibold text-foreground leading-tight">{user?.name}</p>
              <p className="text-[10px] text-muted-foreground">{t(user?.role)}</p>
            </div>
            <ChevronDown className={`w-3.5 h-3.5 text-muted-foreground transition-transform ${profileOpen ? 'rotate-180' : ''}`} />
          </button>
          {profileOpen && (
            <>
              <div className="fixed inset-0 z-[60]" onClick={() => setProfileOpen(false)} />
              <div className="absolute right-0 mt-1 w-56 bg-card rounded-xl shadow-2xl border border-border z-[70] overflow-hidden">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-bold text-foreground">{user?.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
                <button onClick={forceLogout}
                  className="no-fx w-full text-left px-4 py-2.5 text-sm text-destructive hover:bg-destructive/10 flex items-center gap-2 font-semibold"
                  data-testid="logout-dropdown-btn"
                ><LogOut className="w-4 h-4" /> Déconnexion</button>
                <button onClick={logoutAllDevices}
                  className="no-fx w-full text-left px-4 py-2.5 text-sm text-muted-foreground hover:bg-accent flex items-center gap-2 font-medium border-t border-border"
                  data-testid="logout-all-btn"
                ><Monitor className="w-4 h-4" /> Déconnecter tous les appareils</button>
              </div>
            </>
          )}
        </div>
      </header>

      {/* ═══ MOBILE DRAWER OVERLAY ═══ */}
      <AnimatePresence>
        {isMobile && drawerOpen && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30" onClick={() => setDrawerOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* ═══ DESKTOP/TABLET SIDEBAR ═══ */}
      {!isMobile && (
        <aside className="fixed top-0 bottom-0 bg-card border-r border-border z-30 flex flex-col transition-all duration-300"
          style={{ width: sidebarWidth }} data-testid="sidebar"
        >
          <div className={`h-14 flex items-center border-b border-border shrink-0 ${isIconOnly ? 'justify-center px-2' : 'px-4 gap-3'}`}>
            <BeyondExpressLogo size="sm" />
            {!isIconOnly && <span className="text-base font-bold text-foreground tracking-tight">Beyond Express</span>}
          </div>
          <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {filteredNav.map(item => <NavLink key={item.path} item={item} />)}
          </nav>
          <div className="border-t border-border p-2">
            <button onClick={forceLogout}
              className={`no-fx flex w-full items-center gap-3 rounded-lg bg-destructive/90 text-destructive-foreground font-bold text-sm hover:bg-destructive transition-colors
                ${isIconOnly ? 'justify-center p-2.5' : 'px-3 py-2.5'}`}
              data-testid="logout-button"
            >
              <LogOut className="w-[18px] h-[18px] shrink-0" />
              {!isIconOnly && <span>DÉCONNEXION</span>}
            </button>
          </div>
        </aside>
      )}

      {/* ═══ MOBILE SIDE DRAWER ═══ */}
      <AnimatePresence>
        {isMobile && drawerOpen && (
          <motion.aside
            initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-0 bottom-0 w-[280px] bg-card border-r border-border z-40 flex flex-col"
            data-testid="mobile-drawer"
          >
            {/* Drawer header with user info */}
            <div className="p-5 border-b border-border bg-gradient-to-br from-[var(--primary-500)]/10 to-[var(--accent-info)]/5">
              <div className="flex items-center justify-between mb-3">
                <div className="w-11 h-11 rounded-full bg-gradient-to-br from-[var(--primary-500)] to-[var(--accent-info)] flex items-center justify-center text-white font-bold text-lg">
                  {user?.name?.[0]?.toUpperCase()}
                </div>
                <Button variant="ghost" size="icon" onClick={() => setDrawerOpen(false)} className="shrink-0">
                  <X className="w-5 h-5" />
                </Button>
              </div>
              <p className="text-sm font-bold text-foreground">{user?.name}</p>
              <p className="text-xs text-muted-foreground">{t(user?.role)}</p>
            </div>

            <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
              {filteredNav.map(item => <NavLink key={item.path} item={item} mobile />)}
            </nav>

            <div className="border-t border-border p-3 space-y-1.5">
              <button onClick={forceLogout}
                className="no-fx flex w-full items-center gap-3 rounded-lg bg-destructive/90 text-destructive-foreground font-bold text-sm px-3 py-2.5 hover:bg-destructive transition-colors"
                data-testid="drawer-logout-btn"
              ><LogOut className="w-[18px] h-[18px]" /> DÉCONNEXION</button>
              <button onClick={logoutAllDevices}
                className="no-fx flex w-full items-center gap-3 rounded-lg border border-border text-muted-foreground text-xs px-3 py-2 hover:bg-accent transition-colors font-medium"
              ><Monitor className="w-4 h-4" /> Tous les appareils</button>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ═══ MAIN CONTENT ═══ */}
      <main className="pt-14 transition-all duration-300 min-h-screen"
        style={{ paddingLeft: isMobile ? 0 : sidebarWidth }}
      >
        <div className="p-4 md:p-6 lg:p-8">
          <AnimatePresence mode="wait">
            <motion.div key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* ═══ COMMAND BAR ═══ */}
      <CommandBar open={cmdkOpen} onOpenChange={setCmdkOpen} navItems={filteredNav} />

      {/* ═══ AI FAB ═══ */}
      <button
        onClick={() => checkAccess('ai_content_generator') ? setAiOpen(true) : setShowLockModal(true)}
        className={`no-fx fixed z-50 w-12 h-12 text-white rounded-full shadow-lg flex items-center justify-center bottom-6 right-6
          ${checkAccess('ai_content_generator') ? 'bg-gradient-to-br from-[var(--primary-500)] to-[var(--accent-info)] hover:shadow-xl' : 'bg-neutral-400 cursor-not-allowed'}`}
        data-testid="ai-assistant-button"
      ><Bot className="w-5 h-5" /></button>

      {aiOpen && checkAccess('ai_content_generator') && <AIAssistant onClose={() => setAiOpen(false)} />}
      {showLockModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowLockModal(false)}>
          <div onClick={e => e.stopPropagation()}>
            <FeatureLock feature="ai_content_generator" message={getUpgradeMessage('ai_content_generator')} requiredPlan="pro" variant="card" />
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardLayout;
