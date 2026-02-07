import React, { useEffect, useState } from 'react';
import { Command } from 'cmdk';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard, Package, RotateCcw, Warehouse, Settings,
  LogOut, Search, Users, DollarSign, Truck, CreditCard,
  MessageCircle, Bot, Upload, Monitor
} from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

const ICON_MAP = {
  '/dashboard': LayoutDashboard,
  '/dashboard/orders': Package,
  '/dashboard/returns': RotateCcw,
  '/dashboard/warehouse': Warehouse,
  '/dashboard/customers': Users,
  '/dashboard/finance/cod': DollarSign,
  '/dashboard/users/drivers': Truck,
  '/dashboard/subscriptions': CreditCard,
  '/dashboard/whatsapp': MessageCircle,
  '/dashboard/settings/ai': Bot,
  '/dashboard/settings/integrations': Settings,
  '/dashboard/settings/pricing': Settings,
  '/dashboard/orders/import': Upload,
  '/dashboard/products': Package,
};

const CommandBar = ({ open, onOpenChange, navItems = [] }) => {
  const navigate = useNavigate();
  const { forceLogout, logoutAllDevices } = useAuth();
  const [value, setValue] = useState('');

  useEffect(() => {
    if (open) setValue('');
  }, [open]);

  const runAction = (action) => {
    onOpenChange(false);
    action();
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100]" onClick={() => onOpenChange(false)}>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        />
        <div className="flex items-start justify-center pt-[15vh] px-4">
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-[560px]"
            onClick={e => e.stopPropagation()}
          >
            <Command
              className="rounded-2xl border border-border bg-card shadow-2xl overflow-hidden"
              data-testid="command-bar"
              value={value}
              onValueChange={setValue}
            >
              <div className="flex items-center gap-2 px-4 border-b border-border">
                <Search className="w-4 h-4 text-muted-foreground shrink-0" />
                <Command.Input
                  placeholder="Rechercher ou taper une commande..."
                  className="flex-1 h-12 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
                  data-testid="cmdk-input"
                  autoFocus
                />
                <kbd className="text-[10px] font-mono text-muted-foreground bg-muted px-1.5 py-0.5 rounded border border-border">ESC</kbd>
              </div>

              <Command.List className="max-h-[320px] overflow-y-auto p-2">
                <Command.Empty className="py-8 text-center text-sm text-muted-foreground">
                  Aucun résultat
                </Command.Empty>

                <Command.Group heading="Navigation" className="[&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-widest [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5">
                  {navItems.map(item => {
                    const Icon = ICON_MAP[item.path] || LayoutDashboard;
                    return (
                      <Command.Item
                        key={item.path}
                        value={item.label}
                        onSelect={() => runAction(() => navigate(item.path))}
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm cursor-pointer transition-colors
                          text-foreground data-[selected=true]:bg-accent"
                      >
                        <Icon className="w-4 h-4 text-muted-foreground" />
                        <span>{item.label}</span>
                      </Command.Item>
                    );
                  })}
                </Command.Group>

                <Command.Separator className="h-px bg-border my-1" />

                <Command.Group heading="Actions rapides" className="[&_[cmdk-group-heading]]:text-[10px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-widest [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5">
                  <Command.Item value="Déconnexion" onSelect={() => runAction(forceLogout)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm cursor-pointer text-destructive data-[selected=true]:bg-destructive/10"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Déconnexion</span>
                  </Command.Item>
                  <Command.Item value="Déconnecter tous les appareils" onSelect={() => runAction(logoutAllDevices)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm cursor-pointer text-muted-foreground data-[selected=true]:bg-accent"
                  >
                    <Monitor className="w-4 h-4" />
                    <span>Déconnecter tous les appareils</span>
                  </Command.Item>
                </Command.Group>
              </Command.List>

              <div className="flex items-center gap-4 px-4 py-2 border-t border-border text-[10px] text-muted-foreground">
                <span className="flex items-center gap-1"><kbd className="bg-muted px-1 py-0.5 rounded border border-border font-mono">↑↓</kbd> Naviguer</span>
                <span className="flex items-center gap-1"><kbd className="bg-muted px-1 py-0.5 rounded border border-border font-mono">↵</kbd> Sélectionner</span>
                <span className="flex items-center gap-1"><kbd className="bg-muted px-1 py-0.5 rounded border border-border font-mono">ESC</kbd> Fermer</span>
              </div>
            </Command>
          </motion.div>
        </div>
      </div>
    </AnimatePresence>
  );
};

export default CommandBar;
