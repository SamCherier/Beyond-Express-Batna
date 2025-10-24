import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { getDashboardStats, getOrders } from '@/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Package, ShoppingCart, Users, Truck, TrendingUp, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const AdminDashboard = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, ordersRes] = await Promise.all([
        getDashboardStats(),
        getOrders()
      ]);
      setStats(statsRes.data);
      setRecentOrders(ordersRes.data.slice(0, 5));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: t('totalOrders'),
      value: stats?.total_orders || 0,
      icon: <Package className="w-6 h-6" />,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600'
    },
    {
      title: t('totalProducts'),
      value: stats?.total_products || 0,
      icon: <ShoppingCart className="w-6 h-6" />,
      color: 'from-green-500 to-green-600',
      bgColor: 'bg-green-50',
      iconColor: 'text-green-600'
    },
    {
      title: t('totalUsers'),
      value: stats?.total_users || 0,
      icon: <Users className="w-6 h-6" />,
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600'
    },
    {
      title: t('inTransit'),
      value: stats?.in_transit || 0,
      icon: <Truck className="w-6 h-6" />,
      color: 'from-orange-500 to-orange-600',
      bgColor: 'bg-orange-50',
      iconColor: 'text-orange-600'
    }
  ];

  const statusColors = {
    in_stock: '#3B82F6',
    preparing: '#F59E0B',
    in_transit: '#8B5CF6',
    delivered: '#10B981',
    returned: '#EF4444'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-dashboard">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-red-500 to-orange-500 rounded-2xl p-8 text-white shadow-xl">
        <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: 'EB Garamond, serif' }}>
          Bienvenue, {user?.name}! 👋
        </h1>
        <p className="text-red-100" style={{ fontFamily: 'Fira Sans, sans-serif' }}>
          Tableau de bord administrateur - Beyond Express
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, index) => (
          <Card
            key={index}
            className="overflow-hidden border-0 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1"
            data-testid={`stat-card-${index}`}
          >
            <CardContent className="p-0">
              <div className={`h-2 bg-gradient-to-r ${card.color}`}></div>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 ${card.bgColor} rounded-xl flex items-center justify-center`}>
                    <div className={card.iconColor}>{card.icon}</div>
                  </div>
                  <TrendingUp className="w-5 h-5 text-green-500" />
                </div>
                <h3 className="text-gray-600 text-sm font-medium mb-1">{card.title}</h3>
                <p className="text-3xl font-bold text-gray-900">{card.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-red-500" />
              {t('recentOrders')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentOrders.length > 0 ? (
                recentOrders.map((order, index) => (
                  <div
                    key={order.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                    data-testid={`recent-order-${index}`}
                  >
                    <div>
                      <p className="font-medium text-gray-900">{order.tracking_id}</p>
                      <p className="text-sm text-gray-500">{order.recipient.name}</p>
                    </div>
                    <div className="text-right">
                      <span
                        className="px-3 py-1 rounded-full text-xs font-medium"
                        style={{
                          backgroundColor: `${statusColors[order.status]}20`,
                          color: statusColors[order.status]
                        }}
                      >
                        {t(order.status)}
                      </span>
                      <p className="text-sm text-gray-900 mt-1">{order.cod_amount} DA</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-8">Aucune commande récente</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="shadow-lg border-0">
          <CardHeader>
            <CardTitle>Actions rapides</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <button
                className="p-6 rounded-xl bg-gradient-to-br from-red-50 to-orange-50 border border-red-200 hover:shadow-md transition-all hover:-translate-y-1 group"
                data-testid="quick-action-order"
              >
                <Package className="w-8 h-8 text-red-500 mb-3 group-hover:scale-110 transition-transform" />
                <p className="font-medium text-gray-900">Nouvelle commande</p>
              </button>
              <button
                className="p-6 rounded-xl bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 hover:shadow-md transition-all hover:-translate-y-1 group"
                data-testid="quick-action-product"
              >
                <ShoppingCart className="w-8 h-8 text-blue-500 mb-3 group-hover:scale-110 transition-transform" />
                <p className="font-medium text-gray-900">Ajouter produit</p>
              </button>
              <button
                className="p-6 rounded-xl bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 hover:shadow-md transition-all hover:-translate-y-1 group"
                data-testid="quick-action-customer"
              >
                <Users className="w-8 h-8 text-green-500 mb-3 group-hover:scale-110 transition-transform" />
                <p className="font-medium text-gray-900">Nouveau client</p>
              </button>
              <button
                className="p-6 rounded-xl bg-gradient-to-br from-purple-50 to-violet-50 border border-purple-200 hover:shadow-md transition-all hover:-translate-y-1 group"
                data-testid="quick-action-report"
              >
                <TrendingUp className="w-8 h-8 text-purple-500 mb-3 group-hover:scale-110 transition-transform" />
                <p className="font-medium text-gray-900">Voir rapports</p>
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminDashboard;