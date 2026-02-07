import React, { useState, useEffect, useCallback } from 'react';
import { Warehouse as WarehouseIcon, TrendingUp, AlertTriangle, Package, Thermometer, Shield, Box, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

const API = process.env.REACT_APP_BACKEND_URL;

const ZONE_COLORS = { cyan: '#06b6d4', green: '#10b981', orange: '#f59e0b', purple: '#8b5cf6', red: '#ef4444' };
const ZONE_ICONS = { cold: Thermometer, dry: Box, fragile: Shield, standard: Package };

const WAREHOUSE_ZONES = [
  { id: 'A1', name: 'Zone Froide A1', type: 'cold', capacity: 100, used: 68, color: 'cyan', temperature: '4 C' },
  { id: 'A2', name: 'Zone Seche A2', type: 'dry', capacity: 200, used: 170, color: 'green', temperature: '20 C' },
  { id: 'B1', name: 'Zone Fragile B1', type: 'fragile', capacity: 150, used: 95, color: 'orange', temperature: '18 C' },
  { id: 'B2', name: 'Zone Standard B2', type: 'standard', capacity: 300, used: 255, color: 'purple', temperature: '22 C' },
];

const DEPOT_STATS = [
  { city: 'Alger', capacity: 85, status: 'warning' },
  { city: 'Oran', capacity: 62, status: 'optimal' },
  { city: 'Constantine', capacity: 91, status: 'critical' },
  { city: 'Batna', capacity: 45, status: 'optimal' },
];

const WarehousePage = () => {
  const [returnsCount, setReturnsCount] = useState(null);

  const token = localStorage.getItem('token') || document.cookie.split(';').find(c => c.trim().startsWith('session_token='))?.split('=')?.[1];
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const fetchReturnsCount = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/returns/stats`, { headers, credentials: 'include' });
      if (res.ok) setReturnsCount(await res.json());
    } catch (e) { /* noop */ }
  }, []);

  useEffect(() => { fetchReturnsCount(); }, [fetchReturnsCount]);

  const totalCapacity = WAREHOUSE_ZONES.reduce((s, z) => s + z.capacity, 0);
  const totalUsed = WAREHOUSE_ZONES.reduce((s, z) => s + z.used, 0);
  const overallPct = Math.round((totalUsed / totalCapacity) * 100);

  return (
    <div className="space-y-6" data-testid="warehouse-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground flex items-center gap-2" data-testid="warehouse-title">
            <WarehouseIcon className="w-7 h-7 text-[var(--aurora-primary)]" />
            Visual Warehouse
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Gestion intelligente de capacité & zones de stockage</p>
        </div>
        <Button variant="outline" onClick={fetchReturnsCount} data-testid="refresh-warehouse">
          <RefreshCw className="w-4 h-4 mr-2" /> Actualiser
        </Button>
      </div>

      {/* Overall Capacity */}
      <Card>
        <CardContent className="p-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h2 className="text-lg font-bold text-foreground">Capacité Globale</h2>
              <p className="text-sm text-muted-foreground">{totalUsed} / {totalCapacity} emplacements</p>
            </div>
            <div className="text-right">
              <p className="text-4xl font-bold text-foreground">{overallPct}%</p>
              <p className={`text-xs font-semibold ${overallPct > 80 ? 'text-[var(--aurora-error)]' : 'text-[var(--aurora-success)]'}`}>
                {overallPct > 80 ? 'Alerte Capacité' : 'Optimal'}
              </p>
            </div>
          </div>

          {/* Segmented bar */}
          <div className="relative h-6 bg-muted rounded-full overflow-hidden flex">
            {WAREHOUSE_ZONES.map((zone) => {
              const pct = (zone.used / totalCapacity) * 100;
              return (
                <motion.div key={zone.id} initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.6 }}
                  style={{ backgroundColor: ZONE_COLORS[zone.color] }}
                  className="h-full"
                  title={`${zone.name}: ${zone.used}/${zone.capacity}`}
                />
              );
            })}
          </div>

          <div className="flex flex-wrap gap-3 mt-3">
            {WAREHOUSE_ZONES.map(z => (
              <div key={z.id} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: ZONE_COLORS[z.color] }} />
                <span className="text-xs text-muted-foreground">{z.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Zones Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {WAREHOUSE_ZONES.map((zone, i) => {
          const pct = Math.round((zone.used / zone.capacity) * 100);
          const Icon = ZONE_ICONS[zone.type] || Package;
          const status = pct > 85 ? 'critical' : pct > 70 ? 'warning' : 'optimal';

          return (
            <motion.div key={zone.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
              <Card className="hover:shadow-md transition-shadow" data-testid={`zone-${zone.id}`}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-foreground flex items-center gap-2 text-sm">
                    <Icon className="w-4 h-4" style={{ color: ZONE_COLORS[zone.color] }} />
                    {zone.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-center">
                    <div className="w-16 h-16 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${ZONE_COLORS[zone.color]}15` }}>
                      <Icon className="w-8 h-8" style={{ color: ZONE_COLORS[zone.color] }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-muted-foreground">Occupation</span>
                      <span className="text-xs font-bold text-foreground">{pct}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.5, delay: i * 0.1 }}
                        className="h-full rounded-full" style={{ backgroundColor: ZONE_COLORS[zone.color] }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{zone.used}/{zone.capacity}</span>
                    <span style={{ color: ZONE_COLORS[zone.color] }} className="font-semibold">{zone.temperature}</span>
                  </div>

                  <div className={`px-2 py-1 rounded-full text-[10px] font-semibold text-center ${
                    status === 'optimal' ? 'bg-green-100 text-green-700' :
                    status === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {status === 'optimal' ? 'Optimal' : status === 'warning' ? 'Attention' : 'Critique'}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Regional Depots */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-foreground flex items-center gap-2 text-base">
            <TrendingUp className="w-4 h-4 text-[var(--aurora-primary)]" />
            Dépôts Régionaux
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {DEPOT_STATS.map((depot, idx) => (
              <motion.div key={idx} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: idx * 0.08 }}
                className="p-4 rounded-lg border border-border" data-testid={`depot-${depot.city.toLowerCase()}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-foreground text-sm">{depot.city}</h3>
                  <span className={`text-xl font-bold ${
                    depot.status === 'optimal' ? 'text-[var(--aurora-success)]' :
                    depot.status === 'warning' ? 'text-[var(--aurora-warning)]' :
                    'text-[var(--aurora-error)]'
                  }`}>{depot.capacity}%</span>
                </div>
                <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${
                    depot.status === 'optimal' ? 'bg-[var(--aurora-success)]' :
                    depot.status === 'warning' ? 'bg-[var(--aurora-warning)]' :
                    'bg-[var(--aurora-error)]'
                  }`} style={{ width: `${depot.capacity}%` }} />
                </div>
                <p className="text-[10px] text-muted-foreground mt-1.5">
                  {depot.status === 'critical' ? 'Réapprovisionnement urgent' :
                   depot.status === 'warning' ? 'Surveiller' : 'Normal'}
                </p>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Returns integration */}
      {returnsCount && (
        <Card className="border-[var(--aurora-primary)]/20">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[var(--aurora-primary)]/10 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-[var(--aurora-primary)]" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-foreground">Retours en attente de réintégration</p>
              <p className="text-xs text-muted-foreground mt-0.5">{returnsCount.pending || 0} retours en attente - {returnsCount.restocked || 0} déjà remis en stock</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => window.location.href = '/dashboard/returns'} data-testid="go-returns-btn">
              Voir Retours
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WarehousePage;
