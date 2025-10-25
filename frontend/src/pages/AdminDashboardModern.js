import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { getOrders } from '@/api';
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
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalOrders: 0,
    monthRevenue: 0,
    deliveryRate: 0,
    pendingOrders: 0
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await getOrders();
      const ordersData = response.data;
      setOrders(ordersData);
      calculateStats(ordersData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (ordersData) => {
    const total = ordersData.length;
    const delivered = ordersData.filter(o => o.status === 'delivered').length;
    const monthRevenue = ordersData.reduce((sum, o) => sum + (o.cod_amount || 0), 0);
    const pending = ordersData.filter(o => ['in_stock', 'preparing', 'ready_to_ship'].includes(o.status)).length;

    setStats({
      totalOrders: total,
      monthRevenue: monthRevenue,
      deliveryRate: total > 0 ? ((delivered / total) * 100).toFixed(1) : 0,
      pendingOrders: pending
    });
  };

  // Données pour graphique des commandes par statut
  const getOrdersByStatus = () => {
    const statusCount = {
      'En stock': 0,
      'Préparation': 0,
      'Prêt': 0,
      'En transit': 0,
      'Livré': 0,
      'Retourné': 0
    };

    orders.forEach(order => {
      switch(order.status) {
        case 'in_stock': statusCount['En stock']++; break;
        case 'preparing': statusCount['Préparation']++; break;
        case 'ready_to_ship': statusCount['Prêt']++; break;
        case 'in_transit': statusCount['En transit']++; break;
        case 'delivered': statusCount['Livré']++; break;
        case 'returned': statusCount['Retourné']++; break;
        default: break;
      }
    });

    return Object.entries(statusCount).map(([name, value]) => ({ name, value }));
  };

  // Données pour top 5 wilayas
  const getTop5Wilayas = () => {
    const wilayaCount = {};
    orders.forEach(order => {
      const wilaya = order.recipient?.wilaya;
      if (wilaya) {
        wilayaCount[wilaya] = (wilayaCount[wilaya] || 0) + 1;
      }
    });

    return Object.entries(wilayaCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, value]) => ({ name, value }));
  };

  // Données pour évolution des revenus (simulé par jour des 7 derniers jours)
  const getRevenueData = () => {
    const days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
    return days.map((day, index) => ({
      name: day,
      revenus: Math.floor(Math.random() * 50000) + 20000 // Simulé pour demo
    }));
  };

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
      value: `${stats.monthRevenue.toLocaleString()} DA`,
      icon: <DollarSign className="w-8 h-8" />,
      gradient: 'from-green-500 to-emerald-500',
      change: '+23%',
      changeType: 'positive'
    },
    {
      title: 'Taux de Livraison',
      value: `${stats.deliveryRate}%`,
      icon: <CheckCircle className="w-8 h-8" />,
      gradient: 'from-purple-500 to-pink-500',
      change: '+5%',
      changeType: 'positive'
    },
    {
      title: 'En Attente',
      value: stats.pendingOrders,
      icon: <Clock className="w-8 h-8" />,
      gradient: 'from-orange-500 to-red-500',
      change: '-8%',
      changeType: 'negative'
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-red-500"></div>
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

      {/* Charts Row 1 */}
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
              <BarChart data={getOrdersByStatus()}>
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
                  {getOrdersByStatus().map((entry, index) => (
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
              <LineChart data={getRevenueData()}>
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

      {/* Charts Row 2 */}
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
              <BarChart data={getTop5Wilayas()} layout="vertical">
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
                  {getTop5Wilayas().map((entry, index) => (
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
                  <span className="font-medium text-gray-700">Commandes Aujourd'hui</span>
                </div>
                <span className="text-2xl font-bold text-gray-900">{Math.floor(stats.totalOrders * 0.1)}</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                  <span className="font-medium text-gray-700">Livraisons Réussies</span>
                </div>
                <span className="text-2xl font-bold text-gray-900">{orders.filter(o => o.status === 'delivered').length}</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <Clock className="w-5 h-5 text-orange-600" />
                  </div>
                  <span className="font-medium text-gray-700">En Transit</span>
                </div>
                <span className="text-2xl font-bold text-gray-900">{orders.filter(o => o.status === 'in_transit').length}</span>
              </div>

              <div className="flex items-center justify-between p-4 bg-white rounded-xl shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <TrendingDown className="w-5 h-5 text-red-600" />
                  </div>
                  <span className="font-medium text-gray-700">Retours</span>
                </div>
                <span className="text-2xl font-bold text-gray-900">{orders.filter(o => o.status === 'returned').length}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboardModern;
