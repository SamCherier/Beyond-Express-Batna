import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import useFeatureAccess from '@/hooks/useFeatureAccess';
import FeatureLock from '@/components/FeatureLock';
import PlanLimitBanner from '@/components/PlanLimitBanner';
import {
  getDashboardStats,
  getOrdersByStatus,
  getRevenueEvolution,
  getTopWilayas
} from '@/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import {
  Package, TrendingUp, DollarSign, Clock, CheckCircle,
  MapPin, ShoppingBag, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { motion } from 'framer-motion';

const stagger = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } },
};

const STATUS_COLORS = ['#3B82F6', '#8B5CF6', '#F59E0B', '#FF8A3D', '#10B981', '#EF4444'];

const tooltipStyle = {
  backgroundColor: 'hsl(var(--card))',
  border: '1px solid hsl(var(--border))',
  borderRadius: '10px',
  boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
  fontSize: '13px',
};

const AdminDashboardModern = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { checkAccess, getUpgradeMessage } = useFeatureAccess();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ totalOrders: 0, totalUsers: 0, totalProducts: 0, inTransit: 0 });
  const [ordersByStatus, setOrdersByStatus] = useState([]);
  const [revenueData, setRevenueData] = useState([]);
  const [topWilayas, setTopWilayas] = useState([]);

  useEffect(() => { if (user) fetchData(); }, [user]);

  const fetchData = async () => {
    if (!user) { setLoading(false); return; }
    setError(null);
    try {
      const [statsRes, statusRes, revenueRes, wilayasRes] = await Promise.all([
        getDashboardStats(), getOrdersByStatus(), getRevenueEvolution(), getTopWilayas()
      ]);
      setStats({
        totalOrders: statsRes.data.total_orders || 0,
        totalUsers: statsRes.data.total_users || 0,
        totalProducts: statsRes.data.total_products || 0,
        inTransit: statsRes.data.in_transit || 0,
      });
      setOrdersByStatus(statusRes.data || []);
      setRevenueData(revenueRes.data || []);
      setTopWilayas(wilayasRes.data || []);
    } catch (err) {
      setError(err.response?.status ? `Erreur ${err.response.status}` : err.message);
    } finally { setLoading(false); }
  };

  const totalRevenue = revenueData.reduce((s, d) => s + (d.revenus || 0), 0);
  const deliveredCount = ordersByStatus.find(s => s.name === 'Livré')?.value || 0;
  const deliveryRate = stats.totalOrders > 0 ? ((deliveredCount / stats.totalOrders) * 100).toFixed(1) : 0;
  const pendingCount = ordersByStatus.filter(s => ['En stock', 'Préparation', 'Prêt'].includes(s.name)).reduce((s, x) => s + x.value, 0);

  const kpiCards = [
    { title: 'Colis Actifs', value: stats.totalOrders, icon: Package, gradient: 'from-blue-500 to-blue-600', change: '+12%', up: true },
    { title: 'Revenus', value: `${totalRevenue.toLocaleString()} DA`, icon: DollarSign, gradient: 'from-emerald-500 to-emerald-600', change: '+23%', up: true },
    { title: 'Taux Livraison', value: `${deliveryRate}%`, icon: CheckCircle, gradient: 'from-violet-500 to-violet-600', change: '+5%', up: true },
    { title: 'En Attente', value: pendingCount, icon: Clock, gradient: 'from-amber-500 to-amber-600', change: '-8%', up: false },
  ];

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] gap-4">
      <div className="quantum-spinner" />
      <p className="text-muted-foreground text-sm font-medium animate-pulse">Chargement du tableau de bord...</p>
    </div>
  );

  if (!user) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="p-6 bg-amber-50 border border-amber-200 rounded-xl max-w-md text-center">
        <p className="text-amber-900 font-semibold">Connexion requise</p>
        <p className="text-amber-700 text-sm mt-1">Veuillez vous connecter pour voir vos données.</p>
      </div>
    </div>
  );

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6" data-testid="admin-dashboard">
      {/* ── Header ── */}
      <motion.div variants={fadeUp}>
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight" data-testid="dashboard-title">
          Tableau de Bord
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Bienvenue, <span className="font-semibold text-[var(--primary-500)]">{user?.name}</span>
        </p>
      </motion.div>

      <PlanLimitBanner />

      {/* ── KPI Cards ── */}
      <motion.div variants={stagger} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div key={i} variants={fadeUp}>
              <Card className="relative overflow-hidden border-0 shadow-lg hover:shadow-xl transition-shadow group" data-testid={`kpi-${i}`}>
                <div className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-[0.06] group-hover:opacity-[0.1] transition-opacity`} />
                <CardContent className="p-4 sm:p-5 relative z-10">
                  <div className="flex items-start justify-between mb-3">
                    <div className={`p-2.5 rounded-xl bg-gradient-to-br ${card.gradient} text-white shadow-md`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className={`inline-flex items-center gap-0.5 text-xs font-bold px-2 py-0.5 rounded-full
                      ${card.up ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                      {card.up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {card.change}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground font-medium">{card.title}</p>
                  <p className="text-xl sm:text-2xl font-bold text-foreground mt-0.5 tabular-nums">{card.value}</p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>

      {/* ── Error ── */}
      {error && (
        <motion.div variants={fadeUp} className="p-4 rounded-xl border border-destructive/30 bg-destructive/5">
          <p className="text-destructive text-sm font-semibold">Erreur: {error}</p>
        </motion.div>
      )}

      {/* ── Charts Row 1 ── */}
      {checkAccess('pro_dashboard') ? (
        <motion.div variants={stagger} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div variants={fadeUp}>
            <Card className="border shadow-lg">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ShoppingBag className="w-4 h-4 text-[var(--primary-500)]" />
                  Commandes par Statut
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={ordersByStatus} barCategoryGap="20%">
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--neutral-500)' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: 'var(--neutral-500)' }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                      {ordersByStatus.map((_, i) => <Cell key={i} fill={STATUS_COLORS[i % STATUS_COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeUp}>
            <Card className="border shadow-lg">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <TrendingUp className="w-4 h-4 text-[var(--accent-success)]" />
                  Évolution des Revenus
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--neutral-500)' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: 'var(--neutral-500)' }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${v.toLocaleString()} DA`} />
                    <Line type="monotone" dataKey="revenus" stroke="var(--accent-success)" strokeWidth={2.5}
                      dot={{ fill: 'var(--accent-success)', r: 4, strokeWidth: 2, stroke: 'hsl(var(--card))' }}
                      activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      ) : (
        <FeatureLock feature="pro_dashboard" message={getUpgradeMessage('pro_dashboard')} requiredPlan="pro" variant="card" />
      )}

      {/* ── Charts Row 2 ── */}
      {checkAccess('pro_dashboard') ? (
        <motion.div variants={stagger} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div variants={fadeUp}>
            <Card className="border shadow-lg">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <MapPin className="w-4 h-4 text-[var(--primary-500)]" />
                  Top 5 Wilayas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={topWilayas} layout="vertical" barCategoryGap="20%">
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--neutral-500)' }} axisLine={false} tickLine={false} />
                    <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: 'var(--neutral-500)' }} width={85} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                      {topWilayas.map((_, i) => <Cell key={i} fill={STATUS_COLORS[i]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeUp}>
            <Card className="border shadow-lg">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <TrendingUp className="w-4 h-4 text-[var(--accent-info)]" />
                  Performances Clés
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { icon: Package, label: 'Total Commandes', value: stats.totalOrders, color: 'blue' },
                  { icon: CheckCircle, label: 'Livraisons Réussies', value: deliveredCount, color: 'emerald' },
                  { icon: Clock, label: 'En Transit', value: stats.inTransit, color: 'amber' },
                  { icon: TrendingUp, label: 'Retours', value: ordersByStatus.find(s => s.name === 'Retourné')?.value || 0, color: 'red' },
                ].map((item, idx) => {
                  const Icon = item.icon;
                  return (
                    <motion.div key={idx} variants={fadeUp}
                      className="flex items-center justify-between p-3.5 rounded-xl bg-accent/50 hover:bg-accent transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg bg-${item.color}-100`}>
                          <Icon className={`w-4 h-4 text-${item.color}-600`} />
                        </div>
                        <span className="text-sm font-medium text-foreground">{item.label}</span>
                      </div>
                      <span className="text-lg font-bold text-foreground tabular-nums">{item.value}</span>
                    </motion.div>
                  );
                })}
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      ) : (
        <FeatureLock feature="pro_dashboard" message="Plan PRO requis pour le Dashboard Analytics" requiredPlan="pro" variant="card" />
      )}
    </motion.div>
  );
};

export default AdminDashboardModern;
