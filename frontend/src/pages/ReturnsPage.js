import React, { useState, useEffect, useCallback } from 'react';
import { Search, Package, AlertTriangle, CheckCircle, XCircle, TrendingUp, BarChart3, Trash2, Archive, ClipboardCheck, Plus, Loader2, RotateCcw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

const API = process.env.REACT_APP_BACKEND_URL;

const REASON_LABELS = {
  damaged: 'Produit Endommagé',
  absent: 'Client Absent',
  wrong_item: 'Mauvais Produit',
  customer_request: 'Demande Client',
  refused_price: 'Refus (Prix)',
  wrong_address: 'Erreur Adresse',
};

const REASON_COLORS = {
  damaged: 'bg-red-500',
  absent: 'bg-blue-500',
  wrong_item: 'bg-purple-500',
  customer_request: 'bg-orange-500',
  refused_price: 'bg-amber-500',
  wrong_address: 'bg-indigo-500',
};

const STATUS_STYLES = {
  pending: { bg: 'bg-yellow-100 text-yellow-800', label: 'En attente' },
  approved: { bg: 'bg-blue-100 text-blue-800', label: 'Approuvé' },
  rejected: { bg: 'bg-red-100 text-red-800', label: 'Rejeté' },
  restocked: { bg: 'bg-green-100 text-green-800', label: 'Remis en stock' },
  discarded: { bg: 'bg-gray-100 text-gray-800', label: 'Mis au rebut' },
};

const DECISION_ICONS = {
  restock: <Archive className="w-4 h-4" />,
  discard: <Trash2 className="w-4 h-4" />,
  inspect: <ClipboardCheck className="w-4 h-4" />,
};

const ReturnsPage = () => {
  const [returns, setReturns] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ order_id: '', tracking_id: '', customer_name: '', wilaya: '', reason: 'absent', notes: '' });

  const token = localStorage.getItem('token') || document.cookie.split(';').find(c => c.trim().startsWith('session_token='))?.split('=')?.[1];
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const fetchData = useCallback(async () => {
    try {
      const [rRes, sRes] = await Promise.all([
        fetch(`${API}/api/returns`, { headers, credentials: 'include' }),
        fetch(`${API}/api/returns/stats`, { headers, credentials: 'include' }),
      ]);
      if (rRes.ok) setReturns(await rRes.json());
      if (sRes.ok) setStats(await sRes.json());
    } catch (e) {
      console.error('Fetch returns error', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.tracking_id || !form.customer_name || !form.wilaya) {
      toast.error('Remplissez tous les champs obligatoires');
      return;
    }
    setCreating(true);
    try {
      const res = await fetch(`${API}/api/returns`, {
        method: 'POST', headers, credentials: 'include',
        body: JSON.stringify(form),
      });
      if (res.ok) {
        toast.success('Retour créé avec succès');
        setShowCreateModal(false);
        setForm({ order_id: '', tracking_id: '', customer_name: '', wilaya: '', reason: 'absent', notes: '' });
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Erreur de création');
      }
    } catch (e) {
      toast.error('Erreur réseau');
    } finally {
      setCreating(false);
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      const res = await fetch(`${API}/api/returns/${id}`, {
        method: 'PATCH', headers, credentials: 'include',
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        toast.success('Statut mis à jour');
        fetchData();
      }
    } catch (e) {
      toast.error('Erreur de mise à jour');
    }
  };

  const filtered = returns.filter(r =>
    (r.tracking_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (r.customer_name || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const reasonStats = stats?.reason_breakdown || [];
  const totalForPercent = reasonStats.reduce((s, r) => s + r.count, 0) || 1;

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="aurora-spinner" />
    </div>
  );

  return (
    <div className="space-y-6" data-testid="returns-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground flex items-center gap-2" data-testid="returns-title">
            <RotateCcw className="w-7 h-7 text-[var(--aurora-primary)]" />
            Smart Returns - RMA
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Gestion intelligente des retours avec décisions automatiques</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="bg-[var(--aurora-primary)] hover:bg-[var(--aurora-primary)]/90 text-white" data-testid="create-return-btn">
          <Plus className="w-4 h-4 mr-2" /> Nouveau Retour
        </Button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Retours', value: stats?.total ?? 0, icon: TrendingUp, color: 'text-[var(--aurora-primary)]' },
          { label: 'Remis en Stock', value: stats?.restocked ?? 0, icon: Archive, color: 'text-[var(--aurora-success)]' },
          { label: 'Mis au Rebut', value: stats?.discarded ?? 0, icon: Trash2, color: 'text-[var(--aurora-error)]' },
          { label: 'En Attente', value: stats?.pending ?? 0, icon: ClipboardCheck, color: 'text-[var(--aurora-warning)]' },
        ].map((kpi, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Card data-testid={`kpi-${kpi.label.toLowerCase().replace(/\s/g, '-')}`}>
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{kpi.label}</p>
                  <p className="text-2xl font-bold text-foreground mt-1">{kpi.value}</p>
                </div>
                <kpi.icon className={`w-8 h-8 ${kpi.color}`} />
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Returns List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-foreground flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <span className="text-base">Retours ({filtered.length})</span>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input placeholder="Rechercher..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 h-9 text-sm" data-testid="returns-search"
                  />
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {filtered.length === 0 ? (
                <p className="text-center text-muted-foreground py-8 text-sm">Aucun retour trouvé</p>
              ) : (
                <div className="space-y-2">
                  {filtered.map((ret, i) => (
                    <motion.div key={ret.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
                      className="p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors"
                      data-testid={`return-item-${ret.id}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className="font-mono text-sm font-bold text-foreground">{ret.tracking_id}</span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold text-white ${REASON_COLORS[ret.reason] || 'bg-gray-500'}`}>
                              {REASON_LABELS[ret.reason] || ret.reason}
                            </span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${STATUS_STYLES[ret.status]?.bg || 'bg-gray-100 text-gray-600'}`}>
                              {STATUS_STYLES[ret.status]?.label || ret.status}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">{ret.customer_name} - {ret.wilaya}</p>
                          {ret.decision_label && (
                            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                              {DECISION_ICONS[ret.decision]} {ret.decision_label}
                            </p>
                          )}
                        </div>
                        {ret.status === 'pending' && (
                          <div className="flex gap-1 shrink-0">
                            <Button size="sm" variant="outline" className="h-7 text-xs px-2 text-[var(--aurora-success)] border-[var(--aurora-success)]/30"
                              onClick={() => handleStatusChange(ret.id, 'restocked')} data-testid={`approve-${ret.id}`}
                            ><CheckCircle className="w-3 h-3 mr-1" /> Stock</Button>
                            <Button size="sm" variant="outline" className="h-7 text-xs px-2 text-[var(--aurora-error)] border-[var(--aurora-error)]/30"
                              onClick={() => handleStatusChange(ret.id, 'discarded')} data-testid={`discard-${ret.id}`}
                            ><XCircle className="w-3 h-3 mr-1" /> Rebut</Button>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Reason Breakdown */}
        <div>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-foreground flex items-center gap-2 text-base">
                <BarChart3 className="w-4 h-4" /> Motifs de Retour
              </CardTitle>
            </CardHeader>
            <CardContent>
              {reasonStats.length === 0 ? (
                <p className="text-center text-muted-foreground py-4 text-sm">Pas de données</p>
              ) : (
                <div className="space-y-3">
                  {reasonStats.map((stat, idx) => {
                    const pct = Math.round((stat.count / totalForPercent) * 100);
                    return (
                      <div key={idx}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-muted-foreground">{REASON_LABELS[stat.reason] || stat.reason}</span>
                          <span className="text-xs font-bold text-foreground">{pct}%</span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.6, delay: idx * 0.1 }}
                            className={`h-full ${REASON_COLORS[stat.reason] || 'bg-gray-400'}`}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowCreateModal(false)}>
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            className="bg-card rounded-xl border border-border shadow-xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}
            data-testid="create-return-modal"
          >
            <h2 className="text-lg font-bold text-foreground mb-4">Nouveau Retour</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="text-xs text-muted-foreground font-medium">Tracking ID *</label>
                <Input value={form.tracking_id} onChange={e => setForm({ ...form, tracking_id: e.target.value })} placeholder="BEX-XXXXXXXX" data-testid="return-tracking-input" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground font-medium">Nom Client *</label>
                <Input value={form.customer_name} onChange={e => setForm({ ...form, customer_name: e.target.value })} placeholder="Nom complet" data-testid="return-customer-input" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground font-medium">Wilaya *</label>
                <Input value={form.wilaya} onChange={e => setForm({ ...form, wilaya: e.target.value })} placeholder="Ex: Alger" data-testid="return-wilaya-input" />
              </div>
              <div>
                <label className="text-xs text-muted-foreground font-medium">Motif</label>
                <select value={form.reason} onChange={e => setForm({ ...form, reason: e.target.value })}
                  className="w-full h-10 rounded-lg border border-border bg-background px-3 text-sm" data-testid="return-reason-select"
                >
                  {Object.entries(REASON_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground font-medium">Notes</label>
                <Input value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Notes optionnelles" />
              </div>
              <div className="flex gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)} className="flex-1">Annuler</Button>
                <Button type="submit" disabled={creating} className="flex-1 bg-[var(--aurora-primary)] text-white" data-testid="submit-return-btn">
                  {creating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />} Créer
                </Button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default ReturnsPage;
