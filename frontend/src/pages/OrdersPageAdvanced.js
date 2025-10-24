import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { 
  getOrders, createOrder, updateOrderStatus, generateBordereau,
  getTrackingEvents, addTrackingEvent, filterOrdersByDeliveryPartner,
  filterOrdersByUser, getEcommerceUsers
} from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, Search, FileDown, Package, Eye, Clock, MapPin, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const ALGERIAN_WILAYAS = [
  'Adrar', 'Chlef', 'Laghouat', 'Oum El Bouaghi', 'Batna', 'Béjaïa', 'Biskra', 'Béchar', 
  'Blida', 'Bouira', 'Tamanrasset', 'Tébessa', 'Tlemcen', 'Tiaret', 'Tizi Ouzou', 'Alger',
  'Djelfa', 'Jijel', 'Sétif', 'Saïda', 'Skikda', 'Sidi Bel Abbès', 'Annaba', 'Guelma',
  'Constantine', 'Médéa', 'Mostaganem', "M'Sila", 'Mascara', 'Ouargla', 'Oran', 'El Bayadh',
  'Illizi', 'Bordj Bou Arréridj', 'Boumerdès', 'El Tarf', 'Tindouf', 'Tissemsilt', 'El Oued',
  'Khenchela', 'Souk Ahras', 'Tipaza', 'Mila', 'Aïn Defla', 'Naâma', 'Aïn Témouchent',
  'Ghardaïa', 'Relizane'
];

const DELIVERY_PARTNERS = [
  'Yalidine', 'DHD', 'ZR EXPRESS', 'Maystro', 'ECOTRACK', 'NOEST', 
  'GUEPEX', 'KAZI TOUR', 'Lynx Express', 'DHL', 'EMS', 'ARAMEX'
];

const OrdersPageAdvanced = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [wilayaFilter, setWilayaFilter] = useState('all');
  const [deliveryPartnerFilter, setDeliveryPartnerFilter] = useState('all');
  const [ecommerceUserFilter, setEcommerceUserFilter] = useState('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [trackingDialogOpen, setTrackingDialogOpen] = useState(false);
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [trackingEvents, setTrackingEvents] = useState([]);
  const [ecommerceUsers, setEcommerceUsers] = useState([]);
  const [newTrackingEvent, setNewTrackingEvent] = useState({
    status: '',
    location: '',
    notes: ''
  });

  const [formData, setFormData] = useState({
    recipient_name: '',
    recipient_phone: '',
    recipient_address: '',
    recipient_wilaya: '',
    recipient_commune: '',
    cod_amount: '',
    description: '',
    delivery_partner: ''
  });

  useEffect(() => {
    fetchOrders();
    if (user?.role === 'admin') {
      fetchEcommerceUsers();
    }
  }, []);

  useEffect(() => {
    filterOrders();
  }, [orders, searchTerm, statusFilter, wilayaFilter, deliveryPartnerFilter, ecommerceUserFilter]);

  const fetchOrders = async () => {
    try {
      const response = await getOrders();
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Erreur lors du chargement des commandes');
    } finally {
      setLoading(false);
    }
  };

  const fetchEcommerceUsers = async () => {
    try {
      const response = await getEcommerceUsers();
      setEcommerceUsers(response.data);
    } catch (error) {
      console.error('Error fetching ecommerce users:', error);
    }
  };

  const filterOrders = () => {
    let filtered = [...orders];

    if (searchTerm) {
      filtered = filtered.filter(order => 
        order.tracking_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.recipient.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(order => order.status === statusFilter);
    }

    if (wilayaFilter !== 'all') {
      filtered = filtered.filter(order => order.recipient.wilaya === wilayaFilter);
    }

    if (deliveryPartnerFilter !== 'all') {
      filtered = filtered.filter(order => order.delivery_partner === deliveryPartnerFilter);
    }

    if (ecommerceUserFilter !== 'all') {
      filtered = filtered.filter(order => order.user_id === ecommerceUserFilter);
    }

    setFilteredOrders(filtered);
  };

  const handleCreateOrder = async () => {
    try {
      const orderData = {
        recipient: {
          name: formData.recipient_name,
          phone: formData.recipient_phone,
          address: formData.recipient_address,
          wilaya: formData.recipient_wilaya,
          commune: formData.recipient_commune
        },
        cod_amount: parseFloat(formData.cod_amount),
        description: formData.description,
        delivery_partner: formData.delivery_partner
      };

      await createOrder(orderData);
      toast.success('Commande créée avec succès!');
      setCreateDialogOpen(false);
      fetchOrders();
      resetForm();
    } catch (error) {
      console.error('Error creating order:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la création');
    }
  };

  const resetForm = () => {
    setFormData({
      recipient_name: '',
      recipient_phone: '',
      recipient_address: '',
      recipient_wilaya: '',
      recipient_commune: '',
      cod_amount: '',
      description: '',
      delivery_partner: ''
    });
  };

  const handleStatusChange = async (orderId, newStatus) => {
    try {
      await updateOrderStatus(orderId, newStatus);
      toast.success('Statut mis à jour');
      fetchOrders();
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleGenerateBordereau = async () => {
    if (selectedOrders.length === 0) {
      toast.error('Sélectionnez au moins une commande');
      return;
    }

    try {
      const response = await generateBordereau(selectedOrders);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `bordereau_${selectedOrders[0]}.pdf`;
      link.click();
      toast.success('Bordereau généré avec succès!');
    } catch (error) {
      toast.error('Erreur lors de la génération du bordereau');
    }
  };

  const openTrackingDialog = async (order) => {
    setSelectedOrder(order);
    setTrackingDialogOpen(true);
    try {
      const response = await getTrackingEvents(order.id);
      setTrackingEvents(response.data);
    } catch (error) {
      console.error('Error fetching tracking events:', error);
      toast.error('Erreur lors du chargement de l\'historique');
    }
  };

  const handleAddTrackingEvent = async () => {
    if (!newTrackingEvent.status) {
      toast.error('Le statut est requis');
      return;
    }

    try {
      await addTrackingEvent(selectedOrder.id, newTrackingEvent);
      toast.success('Événement ajouté!');
      setNewTrackingEvent({ status: '', location: '', notes: '' });
      
      // Reload tracking events
      const response = await getTrackingEvents(selectedOrder.id);
      setTrackingEvents(response.data);
      
      // Refresh orders list
      fetchOrders();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout de l\'événement');
    }
  };

  const statusColors = {
    in_stock: 'bg-blue-100 text-blue-700 border-blue-200',
    preparing: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    ready_to_ship: 'bg-purple-100 text-purple-700 border-purple-200',
    in_transit: 'bg-orange-100 text-orange-700 border-orange-200',
    delivered: 'bg-green-100 text-green-700 border-green-200',
    returned: 'bg-red-100 text-red-700 border-red-200',
    failed: 'bg-gray-100 text-gray-700 border-gray-200'
  };

  const statusIcons = {
    in_stock: <Package className="w-4 h-4" />,
    preparing: <Clock className="w-4 h-4" />,
    ready_to_ship: <Package className="w-4 h-4" />,
    in_transit: <MapPin className="w-4 h-4" />,
    delivered: <CheckCircle className="w-4 h-4" />,
    returned: <Package className="w-4 h-4" />,
    failed: <Package className="w-4 h-4" />
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="orders-advanced-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>
            {t('orders')} - Tracking Avancé
          </h1>
          <p className="text-gray-600 mt-1">Suivi détaillé et filtres avancés</p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-red-500 hover:bg-red-600" data-testid="create-order-button">
              <Plus className="w-4 h-4 mr-2" />
              {t('createOrder')}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Créer une nouvelle commande</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4 py-4">
              <div className="space-y-2">
                <Label>Nom destinataire *</Label>
                <Input
                  value={formData.recipient_name}
                  onChange={(e) => setFormData({...formData, recipient_name: e.target.value})}
                  placeholder="Nom complet"
                  data-testid="recipient-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Téléphone *</Label>
                <Input
                  value={formData.recipient_phone}
                  onChange={(e) => setFormData({...formData, recipient_phone: e.target.value})}
                  placeholder="0555123456"
                  data-testid="recipient-phone-input"
                />
              </div>
              <div className="col-span-2 space-y-2">
                <Label>Adresse *</Label>
                <Input
                  value={formData.recipient_address}
                  onChange={(e) => setFormData({...formData, recipient_address: e.target.value})}
                  placeholder="Adresse complète"
                  data-testid="recipient-address-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Wilaya *</Label>
                <Select value={formData.recipient_wilaya} onValueChange={(val) => setFormData({...formData, recipient_wilaya: val})}>
                  <SelectTrigger data-testid="recipient-wilaya-select">
                    <SelectValue placeholder="Sélectionner" />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]" position="popper">
                    {ALGERIAN_WILAYAS.map(w => (
                      <SelectItem key={w} value={w}>{w}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Commune *</Label>
                <Input
                  value={formData.recipient_commune}
                  onChange={(e) => setFormData({...formData, recipient_commune: e.target.value})}
                  placeholder="Commune"
                  data-testid="recipient-commune-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Montant COD (DA) *</Label>
                <Input
                  type="number"
                  value={formData.cod_amount}
                  onChange={(e) => setFormData({...formData, cod_amount: e.target.value})}
                  placeholder="0.00"
                  data-testid="cod-amount-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Société de Livraison *</Label>
                <Select value={formData.delivery_partner} onValueChange={(val) => setFormData({...formData, delivery_partner: val})}>
                  <SelectTrigger data-testid="delivery-partner-select">
                    <SelectValue placeholder="Sélectionner transporteur" />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]" position="popper" sideOffset={5}>
                    {DELIVERY_PARTNERS.map(partner => (
                      <SelectItem key={partner} value={partner}>{partner}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2 space-y-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Détails du colis"
                  data-testid="description-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Annuler</Button>
              <Button onClick={handleCreateOrder} className="bg-red-500 hover:bg-red-600" data-testid="submit-order-button">
                Créer la commande
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Advanced Filters */}
      <Card className="border-2 border-red-100">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Rechercher par N° ou nom..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
                data-testid="search-input"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger data-testid="status-filter">
                <SelectValue placeholder="Statut" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les statuts</SelectItem>
                <SelectItem value="in_stock">En stock</SelectItem>
                <SelectItem value="preparing">En préparation</SelectItem>
                <SelectItem value="in_transit">En transit</SelectItem>
                <SelectItem value="delivered">Livré</SelectItem>
                <SelectItem value="returned">Retourné</SelectItem>
              </SelectContent>
            </Select>
            <Select value={wilayaFilter} onValueChange={setWilayaFilter}>
              <SelectTrigger data-testid="wilaya-filter">
                <SelectValue placeholder="Wilaya" />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]" position="popper">
                <SelectItem value="all">Toutes les wilayas</SelectItem>
                {ALGERIAN_WILAYAS.map(w => (
                  <SelectItem key={w} value={w}>{w}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={deliveryPartnerFilter} onValueChange={setDeliveryPartnerFilter}>
              <SelectTrigger data-testid="delivery-partner-filter" className="bg-orange-50 border-orange-200">
                <SelectValue placeholder="🚚 Transporteur" />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]" position="popper">
                <SelectItem value="all">Tous les transporteurs</SelectItem>
                {DELIVERY_PARTNERS.map(p => (
                  <SelectItem key={p} value={p}>{p}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {user?.role === 'admin' && (
              <Select value={ecommerceUserFilter} onValueChange={setEcommerceUserFilter}>
                <SelectTrigger data-testid="ecommerce-user-filter" className="bg-purple-50 border-purple-200">
                  <SelectValue placeholder="👤 Client" />
                </SelectTrigger>
                <SelectContent className="max-h-[300px]" position="popper">
                  <SelectItem value="all">Tous les clients</SelectItem>
                  {ecommerceUsers.map(u => (
                    <SelectItem key={u.id} value={u.id}>{u.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          <div className="mt-3 flex gap-2">
            <Button
              onClick={handleGenerateBordereau}
              variant="outline"
              disabled={selectedOrders.length === 0}
              data-testid="generate-bordereau-button"
            >
              <FileDown className="w-4 h-4 mr-2" />
              Générer Bordereau ({selectedOrders.length})
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card>
        <CardContent className="p-0">
          {filteredOrders.length === 0 ? (
            <div className="text-center py-12">
              <Package className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Aucune commande trouvée</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-6 py-3 text-left">
                      <input type="checkbox" className="rounded" />
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">N° Suivi</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Destinataire</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Wilaya</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Montant</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Transporteur</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Statut</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Tracking</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredOrders.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50" data-testid={`order-row-${order.id}`}>
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          className="rounded"
                          checked={selectedOrders.includes(order.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedOrders([...selectedOrders, order.id]);
                            } else {
                              setSelectedOrders(selectedOrders.filter(id => id !== order.id));
                            }
                          }}
                        />
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-mono text-sm font-medium">{order.tracking_id}</span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-gray-900">{order.recipient.name}</p>
                          <p className="text-sm text-gray-500">{order.recipient.phone}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">{order.recipient.wilaya}</td>
                      <td className="px-6 py-4">
                        <span className="font-semibold text-gray-900">{order.cod_amount} DA</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700">
                          {order.delivery_partner || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Select
                          value={order.status}
                          onValueChange={(val) => handleStatusChange(order.id, val)}
                        >
                          <SelectTrigger className={`w-36 h-8 text-xs border ${statusColors[order.status]}`}>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="in_stock">En stock</SelectItem>
                            <SelectItem value="preparing">Préparation</SelectItem>
                            <SelectItem value="ready_to_ship">Prêt</SelectItem>
                            <SelectItem value="in_transit">En transit</SelectItem>
                            <SelectItem value="delivered">Livré</SelectItem>
                            <SelectItem value="returned">Retourné</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-6 py-4">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openTrackingDialog(order)}
                          data-testid={`tracking-button-${order.id}`}
                          className="hover:bg-red-50 hover:text-red-600 hover:border-red-200"
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          Suivi
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tracking Dialog */}
      <Dialog open={trackingDialogOpen} onOpenChange={setTrackingDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Package className="w-5 h-5 text-red-500" />
              Suivi Détaillé - {selectedOrder?.tracking_id}
            </DialogTitle>
          </DialogHeader>
          
          {selectedOrder && (
            <div className="space-y-6 py-4">
              {/* Order Info */}
              <Card className="bg-gradient-to-r from-red-50 to-orange-50 border-red-100">
                <CardContent className="p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-gray-500">Destinataire</p>
                      <p className="font-medium">{selectedOrder.recipient.name}</p>
                      <p className="text-sm text-gray-600">{selectedOrder.recipient.phone}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Livraison</p>
                      <p className="font-medium">{selectedOrder.recipient.wilaya}</p>
                      <p className="text-sm text-gray-600">{selectedOrder.delivery_partner}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Add New Event (Admin only) */}
              {user?.role === 'admin' && (
                <Card className="border-2 border-blue-100">
                  <CardContent className="p-4">
                    <h3 className="font-semibold mb-3 flex items-center gap-2">
                      <Plus className="w-4 h-4" />
                      Ajouter un événement de tracking
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                      <Select value={newTrackingEvent.status} onValueChange={(val) => setNewTrackingEvent({...newTrackingEvent, status: val})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Statut *" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="in_stock">En stock</SelectItem>
                          <SelectItem value="preparing">En préparation</SelectItem>
                          <SelectItem value="ready_to_ship">Prêt à expédier</SelectItem>
                          <SelectItem value="in_transit">En transit</SelectItem>
                          <SelectItem value="delivered">Livré</SelectItem>
                          <SelectItem value="returned">Retourné</SelectItem>
                        </SelectContent>
                      </Select>
                      <Input
                        placeholder="Localisation (optionnel)"
                        value={newTrackingEvent.location}
                        onChange={(e) => setNewTrackingEvent({...newTrackingEvent, location: e.target.value})}
                      />
                      <div className="col-span-2">
                        <Input
                          placeholder="Notes (optionnel)"
                          value={newTrackingEvent.notes}
                          onChange={(e) => setNewTrackingEvent({...newTrackingEvent, notes: e.target.value})}
                        />
                      </div>
                      <div className="col-span-2">
                        <Button onClick={handleAddTrackingEvent} className="bg-red-500 hover:bg-red-600 w-full">
                          Ajouter l'événement
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Timeline */}
              <div>
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Historique de suivi
                </h3>
                {trackingEvents.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Aucun événement de tracking</p>
                ) : (
                  <div className="space-y-3">
                    {trackingEvents.map((event, index) => (
                      <div key={event.id} className="flex gap-4" data-testid={`tracking-event-${index}`}>
                        <div className="flex flex-col items-center">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${statusColors[event.status]}`}>
                            {statusIcons[event.status]}
                          </div>
                          {index < trackingEvents.length - 1 && (
                            <div className="w-0.5 h-full bg-gray-200 my-1"></div>
                          )}
                        </div>
                        <div className="flex-1 pb-6">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors[event.status]}`}>
                              {t(event.status)}
                            </span>
                            {event.location && (
                              <span className="text-xs text-gray-500 flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                {event.location}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{event.notes || 'Aucune note'}</p>
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(event.timestamp).toLocaleString('fr-FR')}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setTrackingDialogOpen(false)}>Fermer</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OrdersPageAdvanced;
