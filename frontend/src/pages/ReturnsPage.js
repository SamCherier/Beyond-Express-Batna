import React, { useState, useEffect, useCallback } from 'react';
import { Search, AlertTriangle, CheckCircle, XCircle, TrendingUp, BarChart3, Trash2, Archive, ClipboardCheck, Plus, Loader2, RotateCcw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { getReturns, getReturnsStats, createReturn, updateReturnStatus } from '@/api';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.05 } } };
const fadeUp = { hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };

const REASON_LABELS = {
  damaged: 'Endommagé', absent: 'Client Absent', wrong_item: 'Mauvais Produit',
  customer_request: 'Demande Client', refused_price: 'Refus Prix', wrong_address: 'Erreur Adresse',
};
const REASON_COLORS = {
  damaged: 'bg-red-500', absent: 'bg-blue-500', wrong_item: 'bg-violet-500',
  customer_request: 'bg-amber-500', refused_price: 'bg-orange-500', wrong_address: 'bg-indigo-500',
};
const STATUS_MAP = {
  pending: { cls: 'status-in_transit', label: 'En attente' },
  approved: { cls: 'status-delivered', label: 'Approuvé' },
  rejected: { cls: 'status-issue', label: 'Rejeté' },
  restocked: { cls: 'status-delivered', label: 'Remis en stock' },
  discarded: { cls: 'status-pending', label: 'Mis au rebut' },
};

const ReturnsPage = () => {
  const [returns, setReturns] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ order_id: '', tracking_id: '', customer_name: '', wilaya: '', reason: 'absent', notes: '' });

  const fetchData = useCallback(async () => {
    try {
      const [rRes, sRes] = await Promise.allSettled([
        getReturns(),
        getReturnsStats(),
      ]);
      if (rRes.status === 'fulfilled') setReturns(rRes.value.data);
      if (sRes.status === 'fulfilled') setStats(sRes.value.data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.tracking_id || !form.customer_name || !form.wilaya) { toast.error('Champs obligatoires manquants'); return; }
    setCreating(true);
    try {
      await createReturn(form);
      toast.success('Retour créé');
      setShowCreate(false);
      setForm({ order_id: '', tracking_id: '', customer_name: '', wilaya: '', reason: 'absent', notes: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erreur');
    } finally { setCreating(false); }
  };

  const handleStatus = async (id, status) => {
    try {
      await updateReturnStatus(id, status);
      toast.success('Statut mis à jour');
      fetchData();
    } catch { toast.error('Erreur'); }
  };

  const filtered = returns.filter(r =>
    (r.tracking_id || '').toLowerCase().includes(search.toLowerCase()) ||
    (r.customer_name || '').toLowerCase().includes(search.toLowerCase())
  );

  const reasonStats = stats?.reason_breakdown || [];
  const totalForPct = reasonStats.reduce((s, r) => s + r.count, 0) || 1;

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="quantum-spinner" /></div>;

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6" data-testid="returns-page">
      {/* Header */}
      <motion.div variants={fadeUp} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight flex items-center gap-2.5" data-testid="returns-title">
            <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 text-white shadow-md">
              <RotateCcw className="w-5 h-5" />
            </div>
            Smart Returns
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Gestion intelligente des retours avec décisions automatiques</p>
        </div>
        <Button onClick={() => setShowCreate(true)} className="bg-[var(--primary-500)] hover:bg-[var(--primary-500)]/90 text-white shadow-md" data-testid="create-return-btn">
          <Plus className="w-4 h-4 mr-2" /> Nouveau Retour
        </Button>
      </motion.div>

      {/* KPIs */}
      <motion.div variants={stagger} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total', value: stats?.total ?? 0, icon: TrendingUp, gradient: 'from-blue-500 to-blue-600' },
          { label: 'Remis en Stock', value: stats?.restocked ?? 0, icon: Archive, gradient: 'from-emerald-500 to-emerald-600' },
          { label: 'Mis au Rebut', value: stats?.discarded ?? 0, icon: Trash2, gradient: 'from-red-500 to-red-600' },
          { label: 'En Attente', value: stats?.pending ?? 0, icon: ClipboardCheck, gradient: 'from-amber-500 to-amber-600' },
        ].map((kpi, i) => (
          <motion.div key={i} variants={fadeUp}>
            <Card className="border shadow-lg hover:shadow-xl transition-shadow" data-testid={`kpi-${i}`}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground font-medium">{kpi.label}</p>
                  <p className="text-2xl font-bold text-foreground mt-0.5 tabular-nums">{kpi.value}</p>
                </div>
                <div className={`p-2.5 rounded-xl bg-gradient-to-br ${kpi.gradient} text-white shadow-md`}>
                  <kpi.icon className="w-5 h-5" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Returns List */}
        <motion.div variants={fadeUp} className="lg:col-span-2">
          <Card className="border shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-foreground flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <span className="text-base font-semibold">Retours ({filtered.length})</span>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input placeholder="Rechercher..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9 h-9 text-sm" data-testid="returns-search" />
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {filtered.length === 0 ? (
                <p className="text-center text-muted-foreground py-10 text-sm">Aucun retour trouvé</p>
              ) : (
                <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-2">
                  {filtered.map((ret) => (
                    <motion.div key={ret.id} variants={fadeUp}
                      className="p-3.5 rounded-xl border border-border hover:bg-accent/40 transition-colors"
                      data-testid={`return-item-${ret.id}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1.5">
                            <span className="font-mono text-sm font-bold text-foreground">{ret.tracking_id}</span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold text-white ${REASON_COLORS[ret.reason] || 'bg-gray-500'}`}>
                              {REASON_LABELS[ret.reason] || ret.reason}
                            </span>
                            <span className={`status-badge ${STATUS_MAP[ret.status]?.cls || 'status-pending'}`}>
                              {STATUS_MAP[ret.status]?.label || ret.status}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">{ret.customer_name} &mdash; {ret.wilaya}</p>
                          {ret.decision_label && (
                            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1.5">
                              {ret.decision === 'restock' ? <Archive className="w-3 h-3" /> :
                               ret.decision === 'discard' ? <Trash2 className="w-3 h-3" /> :
                               <ClipboardCheck className="w-3 h-3" />}
                              {ret.decision_label}
                            </p>
                          )}
                        </div>
                        {ret.status === 'pending' && (
                          <div className="flex gap-1.5 shrink-0">
                            <Button size="sm" variant="outline" className="h-8 text-xs px-2.5 text-emerald-600 border-emerald-200 hover:bg-emerald-50"
                              onClick={() => handleStatus(ret.id, 'restocked')} data-testid={`approve-${ret.id}`}
                            ><CheckCircle className="w-3.5 h-3.5 mr-1" /> Stock</Button>
                            <Button size="sm" variant="outline" className="h-8 text-xs px-2.5 text-red-600 border-red-200 hover:bg-red-50"
                              onClick={() => handleStatus(ret.id, 'discarded')} data-testid={`discard-${ret.id}`}
                            ><XCircle className="w-3.5 h-3.5 mr-1" /> Rebut</Button>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Reason Breakdown */}
        <motion.div variants={fadeUp}>
          <Card className="border shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-foreground flex items-center gap-2 text-base">
                <BarChart3 className="w-4 h-4 text-[var(--accent-info)]" /> Motifs
              </CardTitle>
            </CardHeader>
            <CardContent>
              {reasonStats.length === 0 ? (
                <p className="text-center text-muted-foreground py-6 text-sm">Pas de données</p>
              ) : (
                <div className="space-y-4">
                  {reasonStats.map((stat, idx) => {
                    const pct = Math.round((stat.count / totalForPct) * 100);
                    return (
                      <div key={idx}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs text-muted-foreground font-medium">{REASON_LABELS[stat.reason] || stat.reason}</span>
                          <span className="text-xs font-bold text-foreground tabular-nums">{pct}%</span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.5, delay: idx * 0.08 }}
                            className={`h-full rounded-full ${REASON_COLORS[stat.reason] || 'bg-gray-400'}`}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowCreate(false)}>
          <motion.div initial={{ opacity: 0, scale: 0.95, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.25 }}
            className="bg-card rounded-2xl border border-border shadow-2xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}
            data-testid="create-return-modal"
          >
            <h2 className="text-lg font-bold text-foreground mb-4">Nouveau Retour</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div><label className="text-xs text-muted-foreground font-semibold">Tracking ID *</label>
                <Input value={form.tracking_id} onChange={e => setForm({ ...form, tracking_id: e.target.value })} placeholder="BEX-XXXXXXXX" data-testid="return-tracking-input" /></div>
              <div><label className="text-xs text-muted-foreground font-semibold">Nom Client *</label>
                <Input value={form.customer_name} onChange={e => setForm({ ...form, customer_name: e.target.value })} placeholder="Nom complet" data-testid="return-customer-input" /></div>
              <div><label className="text-xs text-muted-foreground font-semibold">Wilaya *</label>
                <Input value={form.wilaya} onChange={e => setForm({ ...form, wilaya: e.target.value })} placeholder="Ex: Alger" data-testid="return-wilaya-input" /></div>
              <div><label className="text-xs text-muted-foreground font-semibold">Motif</label>
                <select value={form.reason} onChange={e => setForm({ ...form, reason: e.target.value })}
                  className="w-full h-10 rounded-lg border border-border bg-background px-3 text-sm" data-testid="return-reason-select">
                  {Object.entries(REASON_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select></div>
              <div><label className="text-xs text-muted-foreground font-semibold">Notes</label>
                <Input value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Optionnel" /></div>
              <div className="flex gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreate(false)} className="flex-1">Annuler</Button>
                <Button type="submit" disabled={creating} className="flex-1 bg-[var(--primary-500)] text-white" data-testid="submit-return-btn">
                  {creating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />} Créer
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
};

export default ReturnsPage;
