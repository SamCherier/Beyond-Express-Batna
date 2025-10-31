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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  Package, TrendingUp, DollarSign, ShoppingBag, 
  TrendingDown, MapPin, Clock, CheckCircle 
} from 'lucide-react';

const AdminDashboardModern = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { checkAccess, getUpgradeMessage, currentPlan } = useFeatureAccess();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalOrders: 0,
    totalUsers: 0,
    totalProducts: 0,
    inTransit: 0
  });
  const [ordersByStatus, setOrdersByStatus] = useState([]);
  const [revenueData, setRevenueData] = useState([]);
  const [topWilayas, setTopWilayas] = useState([]);

  useEffect(() => {
    // Only fetch data if user is authenticated
    if (user) {
      fetchData();
    }
  }, [user]);

  const fetchData = async () => {
    // Guard clause: don't fetch if user is not authenticated
    if (!user) {
      console.log('❌ AdminDashboard: No user authenticated, skipping data fetch');
      setLoading(false);
      return;
    }

    console.log('✅ AdminDashboard: User authenticated, fetching dashboard data...', user);
    setError(null);

    try {
      // Fetch all dashboard data in parallel
      console.log('📊 Fetching dashboard endpoints...');
      const [statsRes, statusRes, revenueRes, wilayasRes] = await Promise.all([
        getDashboardStats(),
        getOrdersByStatus(),
        getRevenueEvolution(),
        getTopWilayas()
      ]);

      console.log('✅ Dashboard data received:', {
        stats: statsRes.data,
        ordersByStatus: statusRes.data,
        revenueData: revenueRes.data,
        topWilayas: wilayasRes.data
      });

      setStats({
        totalOrders: statsRes.data.total_orders || 0,
        totalUsers: statsRes.data.total_users || 0,
        totalProducts: statsRes.data.total_products || 0,
        inTransit: statsRes.data.in_transit || 0
      });
      setOrdersByStatus(statusRes.data || []);
      setRevenueData(revenueRes.data || []);
      setTopWilayas(wilayasRes.data || []);
    } catch (error) {
      console.error('❌ Error fetching dashboard data:', error);
      console.error('Error details:', error.response?.data || error.message);
      setError(`Erreur de chargement des données: ${error.response?.status || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Calculate derived stats for KPI cards
  const calculateDerivedStats = () => {
    const totalRevenue = revenueData.reduce((sum, day) => sum + (day.revenus || 0), 0);
    const deliveredCount = ordersByStatus.find(s => s.name === 'Livré')?.value || 0;
    const deliveryRate = stats.totalOrders > 0 
      ? ((deliveredCount / stats.totalOrders) * 100).toFixed(1) 
      : 0;
    const pendingCount = ordersByStatus
      .filter(s => ['En stock', 'Préparation', 'Prêt'].includes(s.name))
      .reduce((sum, s) => sum + s.value, 0);

    return {
      totalRevenue,
      deliveryRate,
      pendingCount
    };
  };

  const derivedStats = calculateDerivedStats();

  // Couleurs pour les graphiques
  const COLORS = {
    primary: '#FF5757',
    secondary: '#FF8A3D',
    blue: '#3B82F6',
    green: '#10B981',
    purple: '#8B5CF6',
    yellow: '#F59E0B',
    red: '#EF4444'
  };

  const STATUS_COLORS = ['#3B82F6', '#8B5CF6', '#F59E0B', '#FF8A3D', '#10B981', '#EF4444'];

  // KPI Cards
  const kpiCards = [
    {
      title: 'Total Commandes',
      value: stats.totalOrders,
      icon: <Package className="w-8 h-8" />,
      gradient: 'from-blue-500 to-cyan-500',
      change: '+12%',
      changeType: 'positive'
    },
    {
      title: 'Revenus du Mois',
      value: `${derivedStats.totalRevenue.toLocaleString()} DA`,
      icon: <DollarSign className="w-8 h-8" />,
      gradient: 'from-green-500 to-emerald-500',
      change: '+23%',
      changeType: 'positive'
    },
    {
      title: 'Taux de Livraison',
      value: `${derivedStats.deliveryRate}%`,
      icon: <CheckCircle className="w-8 h-8" />,
      gradient: 'from-purple-500 to-pink-500',
      change: '+5%',
      changeType: 'positive'
    },
    {
      title: 'En Attente',
      value: derivedStats.pendingCount,
      icon: <Clock className="w-8 h-8" />,
      gradient: 'from-orange-500 to-red-500',
      change: '-8%',
      changeType: 'negative'
    }
  ];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-red-500"></div>
        <p className="text-gray-600">Chargement du tableau de bord...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <div className="p-4 bg-yellow-50 border-2 border-yellow-500 rounded-xl">
          <p className="text-yellow-900 font-semibold">⚠️ Vous devez être connecté pour accéder au dashboard</p>
          <p className="text-yellow-700 text-sm mt-2">Veuillez vous connecter pour voir vos données.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'EB Garamond, serif' }}>
          Tableau de Bord
        </h1>
        <p className="text-gray-600">
          Bienvenue, <span className="font-semibold text-red-500">{user?.name}</span> 👋
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((card, index) => (
          <Card 
            key={index} 
            className="relative overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105"
          >
            {/* Gradient Background */}
            <div className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-10`}></div>
            
            <CardContent className="p-6 relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-gradient-to-br ${card.gradient} text-white shadow-lg`}>
                  {card.icon}
                </div>
                <div className={`text-sm font-semibold px-3 py-1 rounded-full ${
                  card.changeType === 'positive' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {card.change}
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">{card.title}</p>
                <p className="text-3xl font-bold text-gray-900">{card.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-2 border-red-500 rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-500 rounded-full">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-red-900 text-lg">Erreur de Chargement</h3>
              <p className="text-red-700">{error}</p>
              <p className="text-sm text-red-600 mt-2">Veuillez vérifier votre connexion et réessayer. Si le problème persiste, contactez le support.</p>
            </div>
          </div>
        </div>
      )}

      {/* Charts Row 1 */}
      {checkAccess('pro_dashboard') ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Graphique Commandes par Statut */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShoppingBag className="w-5 h-5 text-red-500" />
                Commandes par Statut
              </CardTitle>
              <CardDescription>Répartition des commandes selon leur état actuel</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={ordersByStatus}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" style={{ fontSize: '12px' }} />
                  <YAxis style={{ fontSize: '12px' }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {ordersByStatus.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[index % STATUS_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Graphique Évolution Revenus */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                Évolution des Revenus
              </CardTitle>
              <CardDescription>Revenus générés sur les 7 derniers jours</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" style={{ fontSize: '12px' }} />
                  <YAxis style={{ fontSize: '12px' }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                    }}
                    formatter={(value) => `${value.toLocaleString()} DA`}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="revenus" 
                    stroke={COLORS.green} 
                    strokeWidth={3}
                    dot={{ fill: COLORS.green, r: 5 }}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      ) : (
        <FeatureLock
          feature="pro_dashboard"
          message={getUpgradeMessage('pro_dashboard')}
          requiredPlan="pro"
          variant="card"
        />
      )}

      {/* Charts Row 2 */}
      {checkAccess('pro_dashboard') ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top 5 Wilayas */}
          <Card className="border-0 shadow-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-blue-500" />
                Top 5 Wilayas
              </CardTitle>
              <CardDescription>Wilayas avec le plus grand nombre de commandes</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topWilayas} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" style={{ fontSize: '12px' }} />
                  <YAxis dataKey="name" type="category" style={{ fontSize: '12px' }} width={100} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                    }}
                  />
                  <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                    {topWilayas.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[index]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

        {/* Statistiques Rapides */}
        <Card className="border-0 shadow-xl bg-gradient-to-br from-red-50 to-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-red-500" />
              Statistiques Rapides
            </CardTitle>
            <CardDescription>Aperçu des performances clés</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Package className="w-5 h-5 text-blue-600" />
                  </div>
                  <span className="font-medium text-gray-700">Total Commandes</span>
                </div>
                <span className="text-2xl font-bold text-gray-900">{stats.totalOrders}</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                  <span className="font-medium text-gray-700">Livraisons Réussies</span>
                </div>
                <span className="text-2xl font-bold text-gray-900">
                  {ordersByStatus.find(s => s.name === 'Livré')?.value || 0}
                </span>
              </div>

              <div className="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <Clock className="w-5 h-5 text-orange-600" />
                  </div>
                  <span className="font-medium text-gray-700">En Transit</span>
                </div>
                <span className="text-2xl font-bold text-gray-900">{stats.inTransit}</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <TrendingDown className="w-5 h-5 text-red-600" />
                  </div>
                  <span className="font-medium text-gray-700">Retours</span>
                </div>
                <span className="text-2xl font-bold text-gray-900">
                  {ordersByStatus.find(s => s.name === 'Retourné')?.value || 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboardModern;
