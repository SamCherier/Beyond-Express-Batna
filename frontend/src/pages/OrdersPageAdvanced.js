import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import useFeatureAccess from '@/hooks/useFeatureAccess';
import { useAIDoctor } from '@/hooks/useAIDoctor';
import PlanLimitBanner from '@/components/PlanLimitBanner';
import AIDoctorModal from '@/components/AIDoctorModal';
import api, { 
  getOrders, createOrder, updateOrderStatus, generateBordereau,
  getTrackingEvents, addTrackingEvent, filterOrdersByDeliveryPartner,
  filterOrdersByUser, getEcommerceUsers, sendAIMessage, sendOrderConfirmation,
  shipOrder, bulkShipOrders, smartBulkShip, getActiveCarriers, getShippingLabel, getCarrierStatus, getBulkLabels,
  syncOrderStatus, getOrderTimeline, bulkSyncStatus
} from '@/api';
import TrackingTimeline from '@/components/TrackingTimeline';
import AIPackaging from '@/components/AIPackaging';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, Search, FileDown, Package, Eye, Clock, MapPin, CheckCircle, AlertTriangle, RefreshCw, MessageCircle, Truck, ExternalLink, Send, Loader2, X, Printer } from 'lucide-react';
import { toast } from 'sonner';
import { COMMUNES_BY_WILAYA } from '@/data/communes';

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
  const { checkAccess } = useFeatureAccess();
  const aiDoctor = useAIDoctor();
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
  const [bulkStatusDialogOpen, setBulkStatusDialogOpen] = useState(false);
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [trackingEvents, setTrackingEvents] = useState([]);
  const [ecommerceUsers, setEcommerceUsers] = useState([]);
  const [bulkStatus, setBulkStatus] = useState('');
  const [availableCommunes, setAvailableCommunes] = useState([]);
  const [newTrackingEvent, setNewTrackingEvent] = useState({
    status: '',
    location: '',
    notes: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalOrders, setTotalOrders] = useState(0);
  const [drivers, setDrivers] = useState([]);
  const [assignDriverDialogOpen, setAssignDriverDialogOpen] = useState(false);
  const [selectedDriverId, setSelectedDriverId] = useState('');
  const [activeCarriers, setActiveCarriers] = useState([]);
  const [shipDialogOpen, setShipDialogOpen] = useState(false);
  const [selectedCarrierForShip, setSelectedCarrierForShip] = useState('yalidine');
  const [shipLoading, setShipLoading] = useState(false);
  const [yalidineStatus, setYalidineStatus] = useState({ is_configured: false, is_active: false });
  
  // Unified Tracking System - Control Tower
  const [orderTimeline, setOrderTimeline] = useState(null);
  const [syncingStatus, setSyncingStatus] = useState(false);
  
  // Bulk Shipping Progress State
  const [bulkShipProgress, setBulkShipProgress] = useState({
    isProcessing: false,
    current: 0,
    total: 0,
    successCount: 0,
    failedCount: 0,
    results: []
  });

  const [formData, setFormData] = useState({
    recipient_name: '',
    recipient_phone: '',
    recipient_address: '',
    recipient_wilaya: '',
    recipient_commune: '',
    cod_amount: '',
    description: '',
    delivery_partner: '',
    delivery_type: 'Livraison à Domicile',  // New field
    send_whatsapp_confirmation: false  // New field for automatic WhatsApp confirmation
  });

  useEffect(() => {
    fetchOrders(1);
    if (user?.role === 'admin') {
      fetchEcommerceUsers();
      fetchDrivers();
      fetchActiveCarriers();
      fetchYalidineStatus();
    }
  }, [user]);

  const fetchActiveCarriers = async () => {
    try {
      const response = await getActiveCarriers();
      setActiveCarriers(response.data.carriers || []);
    } catch (error) {
      console.error('Error fetching active carriers:', error);
    }
  };

  const fetchYalidineStatus = async () => {
    try {
      const response = await getCarrierStatus('yalidine');
      setYalidineStatus(response.data);
    } catch (error) {
      console.error('Error fetching Yalidine status:', error);
    }
  };

  const fetchDrivers = async () => {
    try {
      const response = await api.get('/users');
      const allUsers = response.data.users || response.data || [];
      // HARDCORE DEFENSIVE: Triple check it's an array
      const safeUsers = Array.isArray(allUsers) ? allUsers : [];
      const driverUsers = safeUsers.filter(u => u.role === 'delivery');
      setDrivers(Array.isArray(driverUsers) ? driverUsers : []);
    } catch (error) {
      console.error('Error fetching drivers:', error);
      // ALWAYS set empty array on error so page doesn't crash
      setDrivers([]);
    }
  };

  const handleAssignDriver = async () => {
    if (selectedOrders.length === 0) {
      toast.error('Sélectionnez au moins une commande');
      return;
    }

    if (!selectedDriverId) {
      toast.error('Sélectionnez un chauffeur');
      return;
    }

    try {
      // Assign driver to selected orders
      for (const orderId of selectedOrders) {
        await api.patch(`/orders/${orderId}`, {
          delivery_partner: selectedDriverId,
          status: 'IN_TRANSIT'
        });
      }

      toast.success(`${selectedOrders.length} commande(s) assignée(s) au chauffeur`);
      setAssignDriverDialogOpen(false);
      setSelectedDriverId('');
      setSelectedOrders([]);
      fetchOrders(currentPage);
    } catch (error) {
      console.error('Error assigning driver:', error);
      toast.error('Erreur lors de l\'assignation');
    }
  };

  useEffect(() => {
    filterOrders();
  }, [orders, searchTerm, statusFilter, wilayaFilter, deliveryPartnerFilter, ecommerceUserFilter]);

  // Update communes when wilaya changes
  useEffect(() => {
    if (formData.recipient_wilaya && COMMUNES_BY_WILAYA[formData.recipient_wilaya]) {
      setAvailableCommunes(COMMUNES_BY_WILAYA[formData.recipient_wilaya]);
      setFormData(prev => ({ ...prev, recipient_commune: '' }));
    } else {
      setAvailableCommunes([]);
    }
  }, [formData.recipient_wilaya]);

  const fetchOrders = async (page = 1) => {
    try {
      setLoading(true);
      const response = await api.get(`/orders?page=${page}&limit=20`);
      
      // Response now has: {orders: [], total: int, page: int, limit: int, pages: int}
      const { orders: fetchedOrders, total, pages } = response.data;
      
      // No longer calculate risk score for all orders (too slow)
      // Risk score can be calculated on-demand when viewing order details
      setOrders(fetchedOrders);
      setTotalOrders(total);
      setTotalPages(pages);
      setCurrentPage(page);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Erreur lors du chargement des commandes');
    } finally {
      setLoading(false);
    }
  };

  // DISABLED: Risk score calculation is too slow for large order lists
  // Risk score can be calculated on-demand when viewing order details
  const calculateRiskScore = async (order) => {
    // Return default value to avoid errors
    return 'Moyen';
    
    /* ORIGINAL CODE (DISABLED FOR PERFORMANCE)
    try {
      const prompt = `Analyse cette commande et détermine le niveau de risque de fraude (Faible/Moyen/Élevé):
      - Montant COD: ${order.cod_amount} DA
      - Wilaya: ${order.recipient.wilaya}
      - Description: ${order.description || 'N/A'}
      
      Réponds uniquement par: Faible, Moyen, ou Élevé`;
      
      const response = await sendAIMessage(prompt, 'gpt-4o-mini', 'openai', `risk-${order.id}`);
      const risk = response.data.response.trim();
      
      if (risk.includes('Élevé')) return 'high';
      if (risk.includes('Moyen')) return 'medium';
      return 'low';
    } catch (error) {
      console.error('Error calculating risk:', error);
      return 'low';
    }
    */
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
    // Validation frontend avant envoi
    if (!formData.recipient_name?.trim()) {
      aiDoctor.interceptError({ message: "Le nom du destinataire est requis", field: "recipient_name" });
      return;
    }
    if (!formData.recipient_phone?.trim()) {
      aiDoctor.interceptError({ message: "Le téléphone du destinataire est requis", field: "recipient_phone" });
      return;
    }
    if (!formData.recipient_wilaya) {
      aiDoctor.interceptError({ message: "La wilaya est requise", field: "recipient_wilaya" });
      return;
    }
    if (!formData.cod_amount || parseFloat(formData.cod_amount) <= 0) {
      aiDoctor.interceptError({ message: "Le montant COD doit être supérieur à 0", field: "cod_amount" });
      return;
    }

    const createOrderRequest = async () => {
      const orderData = {
        recipient: {
          name: formData.recipient_name.trim(),
          phone: formData.recipient_phone.trim(),
          address: formData.recipient_address?.trim() || "Non spécifiée",
          wilaya: formData.recipient_wilaya,
          commune: formData.recipient_commune || formData.recipient_wilaya
        },
        cod_amount: parseFloat(formData.cod_amount),
        description: formData.description?.trim() || "Commande e-commerce",
        delivery_partner: formData.delivery_partner || null,
        delivery_type: formData.delivery_type || "Livraison à Domicile"
      };

      const response = await createOrder(orderData, formData.send_whatsapp_confirmation);
      
      const successMessage = formData.send_whatsapp_confirmation
        ? '✅ Commande créée avec succès! Confirmation WhatsApp envoyée.'
        : '✅ Commande créée avec succès!';
      
      toast.success(successMessage, {
        description: `N° de suivi: ${response.data.tracking_id}`
      });
      setCreateDialogOpen(false);
      fetchOrders();
      resetForm();
      
      return response;
    };

    try {
      await createOrderRequest();
    } catch (error) {
      console.error('Error creating order:', error);
      // AI Doctor intercepte l'erreur avec possibilité de retry
      aiDoctor.interceptError(error, createOrderRequest);
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
      delivery_partner: '',
      delivery_type: 'Livraison à Domicile',
      send_whatsapp_confirmation: false
    });
    setAvailableCommunes([]);
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

  const handleBulkStatusUpdate = async () => {
    if (selectedOrders.length === 0) {
      toast.error('Sélectionnez au moins une commande');
      return;
    }
    if (!bulkStatus) {
      toast.error('Sélectionnez un statut');
      return;
    }

    try {
      await Promise.all(selectedOrders.map(orderId => updateOrderStatus(orderId, bulkStatus)));
      toast.success(`${selectedOrders.length} commande(s) mise(s) à jour!`);
      setBulkStatusDialogOpen(false);
      setBulkStatus('');
      setSelectedOrders([]);
      fetchOrders();
    } catch (error) {
      toast.error('Erreur lors de la mise à jour en masse');
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
      link.download = `bordereau_${selectedOrders.length}_commandes.pdf`;
      link.click();
      toast.success(`Bordereau généré pour ${selectedOrders.length} commande(s)!`);
    } catch (error) {
      toast.error('Erreur lors de la génération du bordereau');
    }
  };

  const handlePrintLabels = async () => {
    if (selectedOrders.length === 0) {
      toast.error('Sélectionnez au moins une commande');
      return;
    }

    try {
      toast.loading(`🖨️ Génération de ${selectedOrders.length} étiquette(s) A6...`, { id: 'print-labels' });
      
      // Use new unified bulk labels endpoint
      const response = await getBulkLabels(selectedOrders);
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `etiquettes_x${selectedOrders.length}_${new Date().toISOString().slice(0,10)}.pdf`;
      link.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      
      toast.success(`✅ ${selectedOrders.length} étiquette(s) A6 générée(s) !`, { id: 'print-labels' });
    } catch (error) {
      console.error('Error generating labels:', error);
      toast.error('Erreur lors de la génération des étiquettes', { id: 'print-labels' });
    }
  };

  // ===== SHIPPING FUNCTIONS (Smart Router) =====
  const handleShipOrders = async () => {
    if (selectedOrders.length === 0) {
      toast.error('Sélectionnez des commandes à expédier');
      return;
    }

    // Initialize progress
    setBulkShipProgress({
      isProcessing: true,
      current: 0,
      total: selectedOrders.length,
      successCount: 0,
      failedCount: 0,
      results: []
    });
    setShipDialogOpen(false);

    try {
      const response = await bulkShipOrders(selectedOrders, selectedCarrierForShip);
      const { success, failed, results } = response.data;
      
      // Update final progress
      setBulkShipProgress(prev => ({
        ...prev,
        isProcessing: false,
        current: prev.total,
        successCount: success,
        failedCount: failed,
        results: results
      }));
      
      // Show summary toast
      if (success > 0 && failed === 0) {
        toast.success(`🎉 ${success} commande(s) expédiée(s) avec succès!`);
      } else if (success > 0 && failed > 0) {
        toast.warning(`✅ ${success} succès, ❌ ${failed} échec(s)`);
      } else if (failed > 0) {
        toast.error(`❌ Toutes les expéditions ont échoué (${failed})`);
      }
      
      setSelectedOrders([]);
      fetchOrders(currentPage);
      
      // Auto-hide progress bar after 5 seconds
      setTimeout(() => {
        setBulkShipProgress(prev => ({ ...prev, isProcessing: false, results: [] }));
      }, 5000);
      
    } catch (error) {
      console.error('Error shipping orders:', error);
      setBulkShipProgress(prev => ({ ...prev, isProcessing: false }));
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'expédition');
    }
  };

  // NEW: Progressive bulk ship with real-time feedback and SMART ROUTING
  const handleBulkShipWithProgress = async () => {
    if (selectedOrders.length === 0) {
      toast.error('Sélectionnez des commandes à expédier');
      return;
    }

    if (!yalidineStatus.can_ship && activeCarriers.length === 0) {
      toast.error('Aucun transporteur configuré. Allez dans Paramètres → Intégrations');
      return;
    }

    const total = selectedOrders.length;
    
    // Initialize progress
    setBulkShipProgress({
      isProcessing: true,
      current: 0,
      total: total,
      successCount: 0,
      failedCount: 0,
      results: []
    });

    try {
      // 🧠 Use Smart Routing API - AI decides best carrier for each order
      toast.loading('🧠 Analyse AI en cours...', { id: 'smart-ship' });
      
      const response = await smartBulkShip(selectedOrders);
      const { success, failed, results, carrier_summary, smart_routing } = response.data;
      
      toast.dismiss('smart-ship');
      
      // Update final progress
      setBulkShipProgress({
        isProcessing: false,
        current: total,
        total: total,
        successCount: success,
        failedCount: failed,
        results: results || [],
        carrierSummary: carrier_summary
      });

      // Show AI routing summary
      if (carrier_summary && Object.keys(carrier_summary).length > 0) {
        const summaryText = Object.entries(carrier_summary)
          .map(([carrier, count]) => `${carrier}: ${count}`)
          .join(', ');
        toast.success(`🧠 AI Routing: ${summaryText}`, { duration: 5000 });
      }

      // Show main result
      if (success > 0 && failed === 0) {
        toast.success(`🎉 ${success} commande(s) expédiée(s) avec succès!`);
      } else if (success > 0 && failed > 0) {
        toast.warning(`✅ ${success} succès, ❌ ${failed} échec(s)`);
      } else {
        toast.error(`❌ Toutes les expéditions ont échoué`);
      }

      setSelectedOrders([]);
      fetchOrders(currentPage);

      // Auto-hide after 10 seconds
      setTimeout(() => {
        setBulkShipProgress({ isProcessing: false, current: 0, total: 0, successCount: 0, failedCount: 0, results: [] });
      }, 10000);

    } catch (error) {
      console.error('Error in smart shipping:', error);
      setBulkShipProgress(prev => ({ ...prev, isProcessing: false }));
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'expédition intelligente', { id: 'smart-ship' });
    }
  };

  const handleShipSingleOrder = async (order, carrierType = 'yalidine') => {
    try {
      toast.loading(`Expédition via ${carrierType.toUpperCase()}...`, { id: 'ship-single' });
      
      const response = await shipOrder(order.id, carrierType);
      
      if (response.data.success) {
        toast.success(
          `✅ Commande expédiée!\n🚚 Tracking: ${response.data.carrier_tracking_id}`,
          { id: 'ship-single', duration: 5000 }
        );
        fetchOrders(currentPage);
      } else {
        toast.error(`❌ ${response.data.error_message}`, { id: 'ship-single' });
      }
    } catch (error) {
      console.error('Error shipping order:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'expédition', { id: 'ship-single' });
    }
  };

  const handleDownloadCarrierLabel = async (order) => {
    if (!order.carrier_tracking_id) {
      toast.error('Cette commande n\'a pas encore été expédiée');
      return;
    }
    
    try {
      toast.loading('Téléchargement de l\'étiquette...', { id: 'label-download' });
      const response = await getShippingLabel(order.id);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `etiquette_${order.carrier_tracking_id}.pdf`;
      link.click();
      toast.success('Étiquette téléchargée!', { id: 'label-download' });
    } catch (error) {
      console.error('Error downloading label:', error);
      toast.error('Étiquette non disponible', { id: 'label-download' });
    }
  };

  const handleSendWhatsAppConfirmation = async (order) => {
    try {
      // Check if order has phone number
      if (!order.recipient?.phone) {
        toast.error('Cette commande n\'a pas de numéro de téléphone');
        return;
      }

      toast.loading('Envoi de la confirmation WhatsApp...', { id: 'whatsapp-send' });
      
      await sendOrderConfirmation(order.id);
      
      toast.success('✅ Confirmation WhatsApp envoyée avec succès!', { id: 'whatsapp-send' });
    } catch (error) {
      console.error('Error sending WhatsApp confirmation:', error);
      toast.error('❌ Erreur lors de l\'envoi WhatsApp. Vérifiez la configuration Twilio.', { id: 'whatsapp-send' });
    }
  };

  const openTrackingDialog = async (order) => {
    setSelectedOrder(order);
    setTrackingDialogOpen(true);
    setOrderTimeline(null); // Reset timeline
    
    try {
      // Fetch tracking events and timeline in parallel
      const [eventsResponse, timelineResponse] = await Promise.all([
        getTrackingEvents(order.id),
        getOrderTimeline(order.id).catch(() => null) // Don't fail if timeline API fails
      ]);
      
      setTrackingEvents(eventsResponse.data);
      
      if (timelineResponse?.data) {
        setOrderTimeline(timelineResponse.data);
      }
    } catch (error) {
      console.error('Error fetching tracking data:', error);
      toast.error('Erreur lors du chargement de l\'historique');
    }
  };

  // 🔄 Sync Order Status from Carrier (Time Travel for ZR Express Mock)
  const handleSyncStatus = async (orderId) => {
    setSyncingStatus(true);
    try {
      // Force advance for ZR Express mock (Time Travel!)
      const forceAdvance = selectedOrder?.carrier_type === 'zr_express';
      
      const response = await syncOrderStatus(orderId, forceAdvance);
      
      if (response.data.success) {
        if (response.data.status_changed) {
          toast.success(`✅ Statut mis à jour: ${response.data.status_label}`, {
            description: response.data.location || 'Statut synchronisé avec le transporteur'
          });
        } else {
          toast.info('ℹ️ Aucun changement de statut', {
            description: 'Le statut est déjà à jour'
          });
        }
        
        // Refresh timeline and events
        const [eventsResponse, timelineResponse] = await Promise.all([
          getTrackingEvents(orderId),
          getOrderTimeline(orderId)
        ]);
        
        setTrackingEvents(eventsResponse.data);
        setOrderTimeline(timelineResponse.data);
        
        // Update order in local state
        if (response.data.status_changed) {
          setSelectedOrder(prev => ({
            ...prev,
            status: response.data.new_status
          }));
          fetchOrders(); // Refresh main list
        }
      } else {
        toast.error(`❌ Erreur: ${response.data.error || 'Impossible de synchroniser'}`);
      }
    } catch (error) {
      console.error('Error syncing status:', error);
      toast.error('❌ Erreur lors de la synchronisation');
    } finally {
      setSyncingStatus(false);
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
      
      const response = await getTrackingEvents(selectedOrder.id);
      setTrackingEvents(response.data);
      fetchOrders();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout de l\'événement');
    }
  };

  const toggleSelectAll = () => {
    if (selectedOrders.length === filteredOrders.length) {
      setSelectedOrders([]);
    } else {
      setSelectedOrders(filteredOrders.map(o => o.id));
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

  const riskColors = {
    low: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    high: 'bg-red-100 text-red-700'
  };

  const riskLabels = {
    low: 'Faible',
    medium: 'Moyen',
    high: 'Élevé 🚩'
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
      {/* Plan Limit Banner */}
      <PlanLimitBanner />
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>
            {t('orders')} - Tracking Avancé
          </h1>
          <p className="text-gray-600 mt-1">Suivi détaillé, filtres avancés et IA anti-fraude</p>
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
                <Select 
                  value={formData.recipient_commune} 
                  onValueChange={(val) => setFormData({...formData, recipient_commune: val})}
                  disabled={!formData.recipient_wilaya}
                >
                  <SelectTrigger data-testid="recipient-commune-select">
                    <SelectValue placeholder={formData.recipient_wilaya ? "Sélectionner" : "Choisir wilaya d'abord"} />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]" position="popper">
                    {availableCommunes.map(c => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
              <div className="space-y-2">
                <Label>Type de Livraison *</Label>
                <Select value={formData.delivery_type} onValueChange={(val) => setFormData({...formData, delivery_type: val})}>
                  <SelectTrigger data-testid="delivery-type-select">
                    <SelectValue placeholder="Type de livraison" />
                  </SelectTrigger>
                  <SelectContent position="popper" sideOffset={5}>
                    <SelectItem value="Livraison à Domicile">Livraison à Domicile</SelectItem>
                    <SelectItem value="Livraison au Bureau (Stop Desk)">Livraison au Bureau (Stop Desk)</SelectItem>
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
              
              {/* WhatsApp Confirmation Checkbox */}
              <div className={`col-span-2 flex items-center gap-2 p-3 border rounded-lg ${
                checkAccess('whatsapp_auto_confirmation') 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-gray-50 border-gray-200 opacity-50'
              }`}>
                <input
                  type="checkbox"
                  id="whatsapp-confirmation"
                  checked={formData.send_whatsapp_confirmation}
                  onChange={(e) => setFormData({...formData, send_whatsapp_confirmation: e.target.checked})}
                  disabled={!checkAccess('whatsapp_auto_confirmation')}
                  className={`w-4 h-4 border-gray-300 rounded focus:ring-green-500 ${
                    checkAccess('whatsapp_auto_confirmation') 
                      ? 'text-green-600 cursor-pointer' 
                      : 'text-gray-400 cursor-not-allowed'
                  }`}
                />
                <label htmlFor="whatsapp-confirmation" className={`flex items-center gap-2 text-sm ${
                  checkAccess('whatsapp_auto_confirmation') ? 'cursor-pointer' : 'cursor-not-allowed'
                }`}>
                  <MessageCircle className={`w-4 h-4 ${
                    checkAccess('whatsapp_auto_confirmation') ? 'text-green-600' : 'text-gray-400'
                  }`} />
                  <span className={`font-medium ${
                    checkAccess('whatsapp_auto_confirmation') ? 'text-gray-700' : 'text-gray-400'
                  }`}>
                    Envoyer une confirmation WhatsApp automatiquement
                  </span>
                  {!checkAccess('whatsapp_auto_confirmation') && (
                    <span className="ml-2 text-xs text-orange-600 font-semibold">(Plan STARTER requis)</span>
                  )}
                </label>
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
            <Button
              onClick={handlePrintLabels}
              variant="default"
              className="bg-red-600 hover:bg-red-700"
              disabled={selectedOrders.length === 0}
              data-testid="print-labels-button"
            >
              <Package className="w-4 h-4 mr-2" />
              Imprimer Étiquettes ({selectedOrders.length})
            </Button>
            <Button
              onClick={() => setAssignDriverDialogOpen(true)}
              variant="default"
              className="bg-blue-600 hover:bg-blue-700"
              disabled={selectedOrders.length === 0}
              data-testid="assign-driver-button"
            >
              <Truck className="w-4 h-4 mr-2" />
              Assigner Chauffeur ({selectedOrders.length})
            </Button>
            
            {/* SMART SHIPPING BUTTON */}
            <Dialog open={shipDialogOpen} onOpenChange={setShipDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  variant="default"
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-lg"
                  disabled={selectedOrders.length === 0 || activeCarriers.length === 0}
                  data-testid="ship-orders-button"
                >
                  <Send className="w-4 h-4 mr-2" />
                  🚀 Expédier ({selectedOrders.length})
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2 text-xl">
                    <Truck className="w-6 h-6 text-green-600" />
                    Expédition Automatique
                  </DialogTitle>
                </DialogHeader>
                <div className="py-4 space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-sm text-green-800 font-medium">
                      🧠 Smart Router activé
                    </p>
                    <p className="text-xs text-green-700 mt-1">
                      {selectedOrders.length} commande(s) seront envoyées au transporteur choisi
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="font-semibold">Transporteur</Label>
                    {activeCarriers.length > 0 ? (
                      <Select value={selectedCarrierForShip} onValueChange={setSelectedCarrierForShip}>
                        <SelectTrigger className="border-green-200">
                          <SelectValue placeholder="Sélectionner un transporteur" />
                        </SelectTrigger>
                        <SelectContent>
                          {activeCarriers.map(c => (
                            <SelectItem key={c.carrier_type} value={c.carrier_type}>
                              <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                {c.carrier_name}
                                {c.test_mode && <span className="text-xs text-orange-500">(Test)</span>}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <div className="text-center p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <p className="text-sm text-yellow-800">
                          ⚠️ Aucun transporteur configuré
                        </p>
                        <Button
                          variant="link"
                          className="text-yellow-600 mt-2"
                          onClick={() => window.location.href = '/dashboard/settings/integrations'}
                        >
                          Configurer maintenant →
                        </Button>
                      </div>
                    )}
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
                    <p className="font-medium mb-1">Ce qui va se passer :</p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li>Envoi des commandes à l'API {selectedCarrierForShip?.toUpperCase()}</li>
                      <li>Récupération des codes de suivi officiels</li>
                      <li>Mise à jour automatique du statut</li>
                    </ul>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShipDialogOpen(false)}>
                    Annuler
                  </Button>
                  <Button
                    onClick={handleShipOrders}
                    disabled={shipLoading || activeCarriers.length === 0}
                    className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
                  >
                    {shipLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Expédition...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Confirmer l'expédition
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            
            <Dialog open={bulkStatusDialogOpen} onOpenChange={setBulkStatusDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  variant="outline"
                  disabled={selectedOrders.length === 0}
                  className="border-purple-200 hover:bg-purple-50"
                  data-testid="bulk-update-button"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Mettre à jour statut ({selectedOrders.length})
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Mise à jour en masse</DialogTitle>
                </DialogHeader>
                <div className="py-4">
                  <p className="text-sm text-gray-600 mb-4">
                    {selectedOrders.length} commande(s) sélectionnée(s)
                  </p>
                  <Select value={bulkStatus} onValueChange={setBulkStatus}>
                    <SelectTrigger>
                      <SelectValue placeholder="Nouveau statut" />
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
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setBulkStatusDialogOpen(false)}>Annuler</Button>
                  <Button onClick={handleBulkStatusUpdate} className="bg-purple-500 hover:bg-purple-600">
                    Mettre à jour
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
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
                      <input 
                        type="checkbox" 
                        className="rounded" 
                        checked={selectedOrders.length === filteredOrders.length}
                        onChange={toggleSelectAll}
                        data-testid="select-all-checkbox"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">N° Suivi</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Destinataire</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Wilaya</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Montant</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Transporteur</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Score Risque</th>
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
                        <span className={`px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1 w-fit ${riskColors[order.risk_score || 'low']}`}>
                          {order.risk_score === 'high' && <AlertTriangle className="w-3 h-3" />}
                          {riskLabels[order.risk_score || 'low']}
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
                        <div className="flex items-center gap-2">
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
                          
                          {/* Public Tracking Page Link */}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => window.open(`/tracking/${order.tracking_id}`, '_blank')}
                            className="hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200"
                            title="Voir la page publique de tracking"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </Button>
                          
                          {order.recipient?.phone && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleSendWhatsAppConfirmation(order)}
                              disabled={!checkAccess('whatsapp_auto_confirmation')}
                              className={`${
                                checkAccess('whatsapp_auto_confirmation')
                                  ? 'hover:bg-green-50 hover:text-green-600 hover:border-green-200'
                                  : 'opacity-50 cursor-not-allowed'
                              }`}
                              title={checkAccess('whatsapp_auto_confirmation') 
                                ? "Envoyer confirmation WhatsApp" 
                                : "Plan STARTER requis pour WhatsApp"
                              }
                            >
                              <MessageCircle className="w-4 h-4" />
                            </Button>
                          )}
                          
                          {/* SHIP BUTTON - Only if carrier is active and order not shipped */}
                          {activeCarriers.length > 0 && !order.carrier_tracking_id && (
                            <Button
                              size="sm"
                              variant="default"
                              onClick={() => handleShipSingleOrder(order, activeCarriers[0]?.carrier_type || 'yalidine')}
                              className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
                              title="Expédier via transporteur"
                            >
                              <Send className="w-4 h-4" />
                            </Button>
                          )}
                          
                          {/* DOWNLOAD CARRIER LABEL - If already shipped */}
                          {order.carrier_tracking_id && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDownloadCarrierLabel(order)}
                              className="hover:bg-orange-50 hover:text-orange-600 hover:border-orange-200"
                              title={`Télécharger étiquette ${order.carrier_type?.toUpperCase()} - ${order.carrier_tracking_id}`}
                            >
                              <Package className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Pagination Controls */}
          {totalPages > 1 && (
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

              {/* 🧠 AI PACKAGING OPTIMIZER - The WOW Feature! */}
              <AIPackaging order={selectedOrder} />

              {/* YALIDINE SHIPPING BUTTON - Magic Button! */}
              {user?.role === 'admin' && !selectedOrder.carrier_tracking_id && (
                <Card className={`border-2 ${yalidineStatus.can_ship ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${yalidineStatus.can_ship ? 'bg-green-100' : 'bg-gray-100'}`}>
                          <Truck className={`w-6 h-6 ${yalidineStatus.can_ship ? 'text-green-600' : 'text-gray-400'}`} />
                        </div>
                        <div>
                          <h3 className="font-semibold">Expédier avec Yalidine</h3>
                          <p className="text-xs text-gray-500">
                            {yalidineStatus.can_ship 
                              ? `${yalidineStatus.test_mode ? '🧪 Mode Test' : '🚀 Production'} - Prêt à expédier`
                              : yalidineStatus.is_configured 
                                ? '⚠️ Inactif - Testez la connexion'
                                : '❌ Non configuré'
                            }
                          </p>
                        </div>
                      </div>
                      
                      {yalidineStatus.can_ship ? (
                        <Button
                          onClick={() => handleShipSingleOrder(selectedOrder, 'yalidine')}
                          disabled={shipLoading}
                          className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-lg"
                        >
                          {shipLoading ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Envoi en cours...
                            </>
                          ) : (
                            <>
                              <Send className="w-4 h-4 mr-2" />
                              Expédier maintenant
                            </>
                          )}
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          onClick={() => window.location.href = '/dashboard/settings/integrations'}
                          className="border-orange-300 text-orange-600 hover:bg-orange-50"
                        >
                          Configurer →
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* CARRIER INFO - If already shipped */}
              {selectedOrder.carrier_tracking_id && (
                <Card className="border-2 border-blue-200 bg-blue-50">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full flex items-center justify-center bg-blue-100">
                          <CheckCircle className="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold">Expédié via {selectedOrder.carrier_type?.toUpperCase() || 'Yalidine'}</h3>
                          <p className="text-sm text-blue-600 font-mono">{selectedOrder.carrier_tracking_id}</p>
                        </div>
                      </div>
                      
                      <Button
                        variant="outline"
                        onClick={() => handleDownloadCarrierLabel(selectedOrder)}
                        className="border-blue-300 text-blue-600 hover:bg-blue-100"
                      >
                        <Package className="w-4 h-4 mr-2" />
                        Étiquette PDF
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 🚀 UNIFIED TRACKING SYSTEM - Visual Timeline */}
              {selectedOrder.carrier_tracking_id && (
                <TrackingTimeline
                  timeline={orderTimeline?.timeline || [
                    { status: 'pending', label: 'En attente', icon: '⏳', completed: selectedOrder.status !== 'pending' && selectedOrder.status !== 'in_stock', current: selectedOrder.status === 'pending' || selectedOrder.status === 'in_stock' },
                    { status: 'preparing', label: 'Préparation', icon: '📦', completed: ['ready_to_ship', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered'].includes(selectedOrder.status), current: selectedOrder.status === 'preparing' },
                    { status: 'in_transit', label: 'En transit', icon: '🚚', completed: ['out_for_delivery', 'delivered'].includes(selectedOrder.status), current: selectedOrder.status === 'in_transit' },
                    { status: 'out_for_delivery', label: 'En livraison', icon: '🏃', completed: selectedOrder.status === 'delivered', current: selectedOrder.status === 'out_for_delivery' },
                    { status: 'delivered', label: 'Livré', icon: '✅', completed: false, current: selectedOrder.status === 'delivered' },
                  ]}
                  currentStatus={selectedOrder.status}
                  terminalStatus={orderTimeline?.terminal_status}
                  carrierType={selectedOrder.carrier_type}
                  carrierTrackingId={selectedOrder.carrier_tracking_id}
                  lastSyncAt={orderTimeline?.last_sync_at}
                  onSync={() => handleSyncStatus(selectedOrder.id)}
                  syncing={syncingStatus}
                />
              )}

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
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${statusColors[event.status]}`}>
                            {statusIcons[event.status]}
                          </div>
                          {index < trackingEvents.length - 1 && (
                            <div className="w-0.5 h-full bg-gray-200 my-1"></div>
                          )}
                        </div>
                        <div className="flex-1 pb-6">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium border ${statusColors[event.status]}`}>
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

      {/* Assign Driver Dialog */}
      <Dialog open={assignDriverDialogOpen} onOpenChange={setAssignDriverDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assigner un Chauffeur</DialogTitle>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <p className="text-sm text-gray-600">
              {selectedOrders.length} commande(s) sélectionnée(s)
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sélectionner un chauffeur
              </label>
              <select
                value={selectedDriverId}
                onChange={(e) => setSelectedDriverId(e.target.value)}
                className="w-full p-2 border rounded-md"
              >
                <option value="">-- Choisir un chauffeur --</option>
                {(drivers || []).map(driver => (
                  <option key={driver.id} value={driver.id}>
                    {driver.name} ({driver.email})
                  </option>
                ))}
              </select>
              {drivers.length === 0 && (
                <p className="text-sm text-amber-600 mt-2">
                  ⚠️ Aucun chauffeur disponible. Créez d'abord un compte chauffeur.
                </p>
              )}
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                💡 Les commandes seront marquées comme "EN TRANSIT" et assignées au chauffeur sélectionné.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAssignDriverDialogOpen(false)}>
              Annuler
            </Button>
            <Button onClick={handleAssignDriver}>
              <Truck className="w-4 h-4 mr-2" />
              Assigner
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ========== FLOATING ACTION BAR (Bulk Shipping Center) ========== */}
      {selectedOrders.length > 0 && !bulkShipProgress.isProcessing && bulkShipProgress.results.length === 0 && (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-t-2 border-green-500 shadow-2xl animate-in slide-in-from-bottom duration-300">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              {/* Selection Info */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center">
                    <span className="text-white font-bold text-lg">{selectedOrders.length}</span>
                  </div>
                  <div className="text-white">
                    <p className="font-semibold">commande{selectedOrders.length > 1 ? 's' : ''} sélectionnée{selectedOrders.length > 1 ? 's' : ''}</p>
                    <p className="text-xs text-gray-400">Prêt pour l'expédition en masse</p>
                  </div>
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedOrders([])}
                  className="text-gray-400 hover:text-white hover:bg-gray-700"
                >
                  <X className="w-4 h-4 mr-1" />
                  Désélectionner
                </Button>
              </div>
              
              {/* Action Buttons */}
              <div className="flex items-center gap-3">
                {/* Print Labels Button - A6 Thermal */}
                <Button
                  variant="outline"
                  onClick={handlePrintLabels}
                  className="border-gray-600 text-white hover:bg-gray-700 bg-transparent px-4 py-2"
                >
                  <Printer className="w-4 h-4 mr-2" />
                  🖨️ Imprimer A6
                  <span className="ml-2 px-2 py-0.5 text-xs bg-white/20 rounded-full">{selectedOrders.length}</span>
                </Button>
                
                {/* MAIN ACTION: Smart Bulk Ship with AI */}
                <Button
                  onClick={handleBulkShipWithProgress}
                  disabled={activeCarriers.length === 0 && !yalidineStatus.can_ship}
                  className={`px-6 py-3 font-bold text-lg shadow-lg transition-all ${
                    (activeCarriers.length > 0 || yalidineStatus.can_ship)
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white hover:scale-105' 
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <Send className="w-5 h-5 mr-2" />
                  🧠 Expédition Intelligente
                  <span className="ml-2 px-2 py-0.5 text-xs bg-white/20 rounded-full">AI</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========== BULK SHIPPING PROGRESS BAR ========== */}
      {(bulkShipProgress.isProcessing || bulkShipProgress.results.length > 0) && (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-purple-500 shadow-2xl">
          <div className="max-w-7xl mx-auto px-6 py-4">
            {/* Progress Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                {bulkShipProgress.isProcessing ? (
                  <div className="relative">
                    <Loader2 className="w-6 h-6 text-purple-500 animate-spin" />
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full animate-ping"></span>
                  </div>
                ) : bulkShipProgress.failedCount === 0 ? (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-orange-500" />
                )}
                <div>
                  <p className="font-semibold text-gray-900 flex items-center gap-2">
                    {bulkShipProgress.isProcessing 
                      ? `🧠 Routage Intelligent en cours... ${bulkShipProgress.current}/${bulkShipProgress.total}`
                      : `✅ Expédition terminée`
                    }
                    <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">AI Optimized</span>
                  </p>
                  <p className="text-sm text-gray-500">
                    ✅ {bulkShipProgress.successCount} succès
                    {bulkShipProgress.failedCount > 0 && ` • ❌ ${bulkShipProgress.failedCount} échec(s)`}
                  </p>
                </div>
              </div>
              
              {!bulkShipProgress.isProcessing && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setBulkShipProgress({ isProcessing: false, current: 0, total: 0, successCount: 0, failedCount: 0, results: [] })}
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3 mb-3 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  bulkShipProgress.failedCount > 0 
                    ? 'bg-gradient-to-r from-purple-500 via-blue-500 to-orange-500' 
                    : 'bg-gradient-to-r from-purple-500 via-blue-500 to-green-500'
                }`}
                style={{ width: `${(bulkShipProgress.current / Math.max(bulkShipProgress.total, 1)) * 100}%` }}
              />
            </div>
            
            {/* Carrier Summary (when complete) */}
            {!bulkShipProgress.isProcessing && bulkShipProgress.carrierSummary && Object.keys(bulkShipProgress.carrierSummary).length > 0 && (
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm text-gray-600 font-medium">🧠 Routage:</span>
                {Object.entries(bulkShipProgress.carrierSummary).map(([carrier, count]) => (
                  <span 
                    key={carrier}
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      carrier.toLowerCase().includes('yalidine') 
                        ? 'bg-red-100 text-red-700 border border-red-200'
                        : carrier.toLowerCase().includes('zr') 
                          ? 'bg-blue-100 text-blue-700 border border-blue-200'
                          : 'bg-gray-100 text-gray-700 border border-gray-200'
                    }`}
                  >
                    {carrier}: {count}
                  </span>
                ))}
              </div>
            )}
            
            {/* Results Summary (when complete) */}
            {!bulkShipProgress.isProcessing && bulkShipProgress.results.length > 0 && (
              <div className="flex gap-2 overflow-x-auto py-2">
                {bulkShipProgress.results.slice(0, 10).map((result, idx) => (
                  <div 
                    key={idx}
                    className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${
                      result.success 
                        ? result.carrier_name?.toLowerCase().includes('zr')
                          ? 'bg-blue-100 text-blue-700 border border-blue-200'
                          : 'bg-green-100 text-green-700 border border-green-200'
                        : 'bg-red-100 text-red-700 border border-red-200'
                    }`}
                  >
                    {result.success ? (
                      <>
                        {result.carrier_name?.toLowerCase().includes('zr') ? '🚛' : '📦'}
                        {result.carrier_tracking_id || result.order_id?.slice(0,8)}
                      </>
                    ) : (
                      <>❌ {result.order_id?.slice(0,8)}</>
                    )}
                  </div>
                ))}
                {bulkShipProgress.results.length > 10 && (
                  <div className="flex-shrink-0 px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200">
                    +{bulkShipProgress.results.length - 10} autres
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Doctor Modal - Intelligent Error Handler */}
      <AIDoctorModal {...aiDoctor.modalProps} />
    </div>
  );
};

export default OrdersPageAdvanced;
