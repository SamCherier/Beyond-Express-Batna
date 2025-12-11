import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { 
  DollarSign, 
  TrendingUp, 
  Clock, 
  CheckCircle2,
  XCircle,
  Search,
  Download
} from 'lucide-react';
import api from '@/api';

const FinancialCODPage = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalOrders, setTotalOrders] = useState(0);
  const [error, setError] = useState(null);

  // Fetch orders on mount
  useEffect(() => {
    fetchOrders(1);
    fetchSummary();
  }, []);

  const fetchOrders = async (page = 1) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/orders?page=${page}&limit=20`);
      
      // Handle new paginated response format
      if (response.data && response.data.orders) {
        setOrders(response.data.orders || []);
        setTotalOrders(response.data.total || 0);
        setTotalPages(response.data.pages || 1);
        setCurrentPage(page);
      } else {
        // Fallback for old format (if response is direct array)
        setOrders(Array.isArray(response.data) ? response.data : []);
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
      setError('Erreur lors du chargement des commandes');
      setOrders([]); // Set to empty array on error
      toast.error('Erreur lors du chargement des commandes');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await api.get('/financial/financial-summary');
      setSummary(response.data);
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  // Filter orders by tab (DEFENSIVE PROGRAMMING)
  const getFilteredOrders = () => {
    // Always ensure orders is an array
    let filtered = Array.isArray(orders) ? orders : [];

    // Filter by payment status
    if (activeTab !== 'all') {
      filtered = filtered.filter(order => order.payment_status === activeTab);
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(order => 
        order.tracking_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        order.recipient?.name?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    return filtered;
  };

  const filteredOrders = getFilteredOrders();

  // Handle select all
  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedOrders(filteredOrders.map(o => o.id));
    } else {
      setSelectedOrders([]);
    }
  };

  // Handle individual select
  const handleSelectOrder = (orderId, checked) => {
    if (checked) {
      setSelectedOrders([...selectedOrders, orderId]);
    } else {
      setSelectedOrders(selectedOrders.filter(id => id !== orderId));
    }
  };

  // Batch update payment status
  const handleBatchUpdate = async (newStatus) => {
    if (selectedOrders.length === 0) {
      toast.error('Aucune commande sélectionnée');
      return;
    }

    try {
      await api.post('/financial/batch-update-payment', {
        order_ids: selectedOrders,
        new_status: newStatus
      });

      toast.success(`${selectedOrders.length} commandes mises à jour`);
      setSelectedOrders([]);
      fetchOrders();
      fetchSummary();
    } catch (error) {
      console.error('Error batch updating:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  // Payment status badge
  const getStatusBadge = (status) => {
    const statusConfig = {
      unpaid: { label: 'Non Payé', variant: 'secondary', icon: Clock },
      collected_by_driver: { label: 'Encaissé', variant: 'default', icon: DollarSign },
      transferred_to_merchant: { label: 'Transféré', variant: 'success', icon: CheckCircle2 },
      returned: { label: 'Retourné', variant: 'destructive', icon: XCircle }
    };

    const config = statusConfig[status] || statusConfig.unpaid;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="gap-1">
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  // Tab counts
  const getTabCount = (status) => {
    if (status === 'all') return orders.length;
    return orders.filter(o => o.payment_status === status).length;
  };

  if (loading && orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
        <p className="text-gray-600">Chargement des données financières...</p>
      </div>
    );
  }

  if (error && orders.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <XCircle className="w-16 h-16 text-red-500" />
        <p className="text-gray-900 font-semibold">Erreur de chargement</p>
        <p className="text-gray-600">{error}</p>
        <Button onClick={() => fetchOrders(1)}>
          Réessayer
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Hacen Tunisia, serif' }}>
            Gestion Financière COD
          </h1>
          <p className="text-gray-600 mt-1">Réconciliation des paiements Cash on Delivery</p>
        </div>
        <Button variant="outline" className="gap-2">
          <Download className="w-4 h-4" />
          Exporter
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total COD</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.grand_total?.total_cod?.toFixed(2) || 0} DZD
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Encaissé</p>
                <p className="text-2xl font-bold text-green-600">
                  {summary.summary_by_status?.collected_by_driver?.total_cod?.toFixed(2) || 0} DZD
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Transféré</p>
                <p className="text-2xl font-bold text-purple-600">
                  {summary.summary_by_status?.transferred_to_merchant?.total_net?.toFixed(2) || 0} DZD
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">En Attente</p>
                <p className="text-2xl font-bold text-orange-600">
                  {summary.summary_by_status?.unpaid?.total_cod?.toFixed(2) || 0} DZD
                </p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </div>
        </div>
      )}

      {/* Filters & Actions */}
      <div className="bg-white p-4 rounded-lg border shadow-sm space-y-4">
        {/* Tabs */}
        <div className="flex items-center gap-2 border-b pb-3">
          {[
            { key: 'all', label: 'Tout' },
            { key: 'unpaid', label: 'Non Payé' },
            { key: 'collected_by_driver', label: 'Encaissé' },
            { key: 'transferred_to_merchant', label: 'Transféré' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-red-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.label} ({getTabCount(tab.key)})
            </button>
          ))}
        </div>

        {/* Search & Batch Actions */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Rechercher par ID ou nom client..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {selectedOrders.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">{selectedOrders.length} sélectionnée(s)</span>
              <Button
                onClick={() => handleBatchUpdate('collected_by_driver')}
                variant="default"
                size="sm"
              >
                Marquer Encaissé
              </Button>
              <Button
                onClick={() => handleBatchUpdate('transferred_to_merchant')}
                variant="default"
                size="sm"
                className="bg-purple-600 hover:bg-purple-700"
              >
                Marquer Transféré
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-4 text-left">
                  <Checkbox
                    checked={selectedOrders.length === filteredOrders.length && filteredOrders.length > 0}
                    onCheckedChange={handleSelectAll}
                  />
                </th>
                <th className="p-4 text-left text-sm font-semibold text-gray-700">ID Commande</th>
                <th className="p-4 text-left text-sm font-semibold text-gray-700">Date</th>
                <th className="p-4 text-left text-sm font-semibold text-gray-700">Client</th>
                <th className="p-4 text-right text-sm font-semibold text-gray-700">Montant COD</th>
                <th className="p-4 text-right text-sm font-semibold text-gray-700">Livraison</th>
                <th className="p-4 text-right text-sm font-semibold text-gray-700 bg-green-50">NET (À Payer)</th>
                <th className="p-4 text-center text-sm font-semibold text-gray-700">Statut</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan="8" className="p-8 text-center text-gray-500">
                    Aucune commande trouvée
                  </td>
                </tr>
              ) : (
                filteredOrders.map(order => (
                  <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4">
                      <Checkbox
                        checked={selectedOrders.includes(order.id)}
                        onCheckedChange={(checked) => handleSelectOrder(order.id, checked)}
                      />
                    </td>
                    <td className="p-4">
                      <span className="font-mono text-sm text-blue-600">{order.tracking_id}</span>
                    </td>
                    <td className="p-4 text-sm text-gray-600">
                      {new Date(order.created_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="p-4">
                      <div>
                        <p className="font-medium text-gray-900">{order.recipient?.name}</p>
                        <p className="text-sm text-gray-500">{order.recipient?.wilaya}</p>
                      </div>
                    </td>
                    <td className="p-4 text-right font-semibold text-gray-900">
                      {order.cod_amount?.toFixed(2)} DZD
                    </td>
                    <td className="p-4 text-right text-gray-600">
                      {order.shipping_cost?.toFixed(2)} DZD
                    </td>
                    <td className="p-4 text-right font-bold text-green-700 bg-green-50">
                      {order.net_to_merchant?.toFixed(2)} DZD
                    </td>
                    <td className="p-4 text-center">
                      {getStatusBadge(order.payment_status)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Controls */}
        {!loading && !error && totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t">
            <div className="text-sm text-gray-600">
              Page {currentPage} sur {totalPages} ({totalOrders} commande(s) au total)
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchOrders(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Précédent
              </Button>
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const page = i + 1;
                return (
                  <Button
                    key={page}
                    variant={currentPage === page ? "default" : "outline"}
                    size="sm"
                    onClick={() => fetchOrders(page)}
                  >
                    {page}
                  </Button>
                );
              })}
              {totalPages > 5 && <span className="px-2">...</span>}
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchOrders(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Suivant
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialCODPage;
