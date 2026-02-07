import React, { useState, useEffect, useCallback } from 'react';
import { Warehouse as WarehouseIcon, TrendingUp, AlertTriangle, Package, Thermometer, Shield, Box, RefreshCw, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

const API = process.env.REACT_APP_BACKEND_URL;

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };

const ZONE_COLORS = { cyan: '#06b6d4', green: '#10b981', orange: '#f59e0b', purple: '#8b5cf6' };
const ZONE_ICONS = { cold: Thermometer, dry: Box, fragile: Shield, standard: Package };

const WarehousePage = () => {
  const [zones, setZones] = useState([]);
  const [depots, setDepots] = useState([]);
  const [returnsStats, setReturnsStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem('auth_token') || localStorage.getItem('token') || document.cookie.split(';').find(c => c.trim().startsWith('session_token='))?.split('=')?.[1];
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [zRes, dRes, rRes] = await Promise.all([
        fetch(`${API}/api/warehouse/zones`, { headers, credentials: 'include' }),
        fetch(`${API}/api/warehouse/depots`, { headers, credentials: 'include' }),
        fetch(`${API}/api/returns/stats`, { headers, credentials: 'include' }),
      ]);
      if (zRes.ok) setZones(await zRes.json());
      if (dRes.ok) setDepots(await dRes.json());
      if (rRes.ok) setReturnsStats(await rRes.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const totalCap = zones.reduce((s, z) => s + (z.capacity || 0), 0);
  const totalUsed = zones.reduce((s, z) => s + (z.used || 0), 0);
  const overallPct = totalCap > 0 ? Math.round((totalUsed / totalCap) * 100) : 0;

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="quantum-spinner" /></div>;

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6" data-testid="warehouse-page">
      {/* Header */}
      <motion.div variants={fadeUp} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight flex items-center gap-2.5" data-testid="warehouse-title">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md">
              <WarehouseIcon className="w-5 h-5" />
            </div>
            Visual Warehouse
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Capacité & zones de stockage — Données temps réel</p>
        </div>
        <Button variant="outline" onClick={fetchAll} className="shadow-sm" data-testid="refresh-warehouse">
          <RefreshCw className="w-4 h-4 mr-2" /> Actualiser
        </Button>
      </motion.div>

      {/* Overall Capacity (REAL DATA) */}
      <motion.div variants={fadeUp}>
        <Card className="border shadow-lg">
          <CardContent className="p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <div>
                <h2 className="text-lg font-bold text-foreground">Capacité Globale</h2>
                <p className="text-sm text-muted-foreground">{totalUsed} / {totalCap} emplacements</p>
              </div>
              <div className="text-right">
                <p className="text-4xl font-bold text-foreground tabular-nums">{overallPct}%</p>
                <p className={`text-xs font-bold ${overallPct > 80 ? 'text-[var(--accent-error)]' : 'text-[var(--accent-success)]'}`}>
                  {overallPct > 80 ? 'Alerte Capacité' : 'Optimal'}
                </p>
              </div>
            </div>
            {totalCap > 0 && (
              <div className="relative h-5 bg-muted rounded-full overflow-hidden flex">
                {zones.map((z) => (
                  <motion.div key={z.id} initial={{ width: 0 }} animate={{ width: `${(z.used / totalCap) * 100}%` }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                    style={{ backgroundColor: ZONE_COLORS[z.color] || '#6b7280' }} className="h-full"
                    title={`${z.name}: ${z.used}/${z.capacity}`}
                  />
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-4 mt-3">
              {zones.map(z => (
                <div key={z.id} className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: ZONE_COLORS[z.color] || '#6b7280' }} />
                  <span className="text-xs text-muted-foreground">{z.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Zone Cards (FROM DATABASE) */}
      <motion.div variants={stagger} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {zones.map((z, i) => {
          const pct = z.capacity > 0 ? Math.round((z.used / z.capacity) * 100) : 0;
          const Icon = ZONE_ICONS[z.zone_type] || Package;
          const status = pct > 85 ? 'critical' : pct > 70 ? 'warning' : 'optimal';
          return (
            <motion.div key={z.id} variants={fadeUp}>
              <Card className="border shadow-lg hover:shadow-xl transition-shadow" data-testid={`zone-${z.id}`}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-foreground flex items-center gap-2 text-sm">
                    <Icon className="w-4 h-4" style={{ color: ZONE_COLORS[z.color] || '#6b7280' }} />
                    {z.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-center">
                    <div className="w-14 h-14 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${ZONE_COLORS[z.color] || '#6b7280'}15` }}>
                      <Icon className="w-7 h-7" style={{ color: ZONE_COLORS[z.color] || '#6b7280' }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-muted-foreground">Occupation</span>
                      <span className="text-xs font-bold text-foreground tabular-nums">{pct}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.5, delay: i * 0.1 }}
                        className="h-full rounded-full" style={{ backgroundColor: ZONE_COLORS[z.color] || '#6b7280' }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground tabular-nums">{z.used}/{z.capacity}</span>
                    <span style={{ color: ZONE_COLORS[z.color] || '#6b7280' }} className="font-semibold">{z.temperature}</span>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-[10px] font-bold text-center
                    ${status === 'optimal' ? 'bg-emerald-50 text-emerald-700' :
                      status === 'warning' ? 'bg-amber-50 text-amber-700' :
                      'bg-red-50 text-red-700'}`}>
                    {status === 'optimal' ? 'Optimal' : status === 'warning' ? 'Attention' : 'Critique'}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Regional Depots (FROM DATABASE) */}
      <motion.div variants={fadeUp}>
        <Card className="border shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="text-foreground flex items-center gap-2 text-base">
              <TrendingUp className="w-4 h-4 text-[var(--primary-500)]" /> Dépôts Régionaux
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {depots.map((d, idx) => {
                const st = d.capacity_pct > 90 ? 'critical' : d.capacity_pct > 75 ? 'warning' : 'optimal';
                return (
                  <motion.div key={d.id || idx} variants={fadeUp}
                    className="p-4 rounded-xl border border-border hover:bg-accent/40 transition-colors" data-testid={`depot-${d.city?.toLowerCase()}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-bold text-foreground text-sm">{d.city}</h3>
                      <span className={`text-xl font-bold tabular-nums ${
                        st === 'optimal' ? 'text-[var(--accent-success)]' :
                        st === 'warning' ? 'text-[var(--accent-warning)]' :
                        'text-[var(--accent-error)]'
                      }`}>{d.capacity_pct}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${
                        st === 'optimal' ? 'bg-[var(--accent-success)]' :
                        st === 'warning' ? 'bg-[var(--accent-warning)]' :
                        'bg-[var(--accent-error)]'
                      }`} style={{ width: `${d.capacity_pct}%` }} />
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1.5 font-medium">
                      {st === 'critical' ? 'Réapprovisionnement urgent' :
                       st === 'warning' ? 'Surveiller' : 'Normal'}
                    </p>
                  </motion.div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Returns Banner */}
      {returnsStats && (returnsStats.pending > 0 || returnsStats.restocked > 0) && (
        <motion.div variants={fadeUp}>
          <Card className="border border-[var(--primary-500)]/20 shadow-lg">
            <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[var(--primary-500)]/10 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-6 h-6 text-[var(--primary-500)]" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-foreground">Retours en attente de réintégration</p>
                <p className="text-xs text-muted-foreground mt-0.5">{returnsStats.pending || 0} en attente &mdash; {returnsStats.restocked || 0} déjà remis en stock</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => window.location.href = '/dashboard/returns'} data-testid="go-returns-btn">
                Voir Retours
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
};

export default WarehousePage;
