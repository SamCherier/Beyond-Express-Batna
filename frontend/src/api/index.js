import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${API_URL}/api`;

const api = axios.create({
  baseURL: API,
  withCredentials: true
});

// Add auth token to all requests (backup for cross-origin cookie issues)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Handle 401 responses - redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Don't redirect if already on login page or during initial auth check
      const isAuthEndpoint = error.config?.url?.includes('/auth/');
      if (!isAuthEndpoint && !window.location.pathname.includes('/login')) {
        console.warn('Session expired, redirecting to login...');
        // Don't immediately redirect - let the component handle it
      }
    }
    return Promise.reject(error);
  }
);

// Dashboard
export const getDashboardStats = () => api.get('/dashboard/stats');
export const getOrdersByStatus = () => api.get('/dashboard/orders-by-status');
export const getRevenueEvolution = () => api.get('/dashboard/revenue-evolution');
export const getTopWilayas = () => api.get('/dashboard/top-wilayas');

// Orders
export const getOrders = (status) => api.get('/orders', { params: { status } });
export const getOrder = (id) => api.get(`/orders/${id}`);
export const createOrder = (data, sendWhatsAppConfirmation = false) => 
  api.post('/orders', data, { params: { send_whatsapp_confirmation: sendWhatsAppConfirmation } });
export const updateOrderStatus = (id, status) => api.patch(`/orders/${id}/status`, null, { params: { status } });
export const generateBordereau = (orderIds) => 
  api.post('/orders/bordereau', orderIds, { responseType: 'blob' });

// Tracking
export const addTrackingEvent = (orderId, data) => api.post(`/orders/${orderId}/tracking`, data);
export const getTrackingEvents = (orderId) => api.get(`/orders/${orderId}/tracking`);
export const filterOrdersByDeliveryPartner = (partner) => api.get('/orders/filter/by-delivery-partner', { params: { delivery_partner: partner } });
export const filterOrdersByUser = (userId) => api.get('/orders/filter/by-user', { params: { user_id: userId } });
export const getEcommerceUsers = () => api.get('/users/ecommerce');

// Products
export const getProducts = () => api.get('/products');
export const createProduct = (data) => api.post('/products', data);
export const updateProductStock = (id, stock) => api.patch(`/products/${id}/stock`, null, { params: { stock_available: stock } });

// Customers
export const getCustomers = () => api.get('/customers');
export const createCustomer = (data) => api.post('/customers', data);
export const updateCustomer = (id, data) => api.patch(`/customers/${id}`, data);
export const generateCustomerQR = (id) => api.post(`/customers/${id}/generate-qr`, null, { responseType: 'blob' });
export const uploadProfilePicture = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/upload-profile-picture', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

// Delivery Partners
export const getDeliveryPartners = () => api.get('/delivery-partners');
export const createDeliveryPartner = (data) => api.post('/delivery-partners', data);

// Invoices
export const getInvoices = () => api.get('/invoices');

// Organization
export const getOrganization = () => api.get('/organization');
export const updateOrganization = (data) => api.patch('/organization', data);

// API Keys
export const getAPIKeys = () => api.get('/api-keys');
export const createAPIKey = (name) => api.post('/api-keys', null, { params: { name } });

// Support
export const getSupportTickets = () => api.get('/support/tickets');
export const createSupportTicket = (data) => api.post('/support/tickets', data);

// Subscriptions & Plans
export const getAllPlans = () => api.get('/subscriptions/plans');
export const getPlanByType = (planType) => api.get(`/subscriptions/plans/${planType}`);
export const subscribeToPlan = (planType, billingPeriod = 'monthly') => 
  api.post('/subscriptions/subscribe', { plan_type: planType, billing_period: billingPeriod });
export const getMySubscription = () => api.get('/subscriptions/my-subscription');
export const checkFeatureLimit = (feature) => api.get(`/subscriptions/check-limit/${feature}`);
export const cancelSubscription = (reason = null) => 
  api.post('/subscriptions/cancel', { cancellation_reason: reason });
export const upgradeSubscription = (newPlanType, newBillingPeriod = 'monthly') => 
  api.post('/subscriptions/upgrade', { new_plan_type: newPlanType, new_billing_period: newBillingPeriod });

// Carriers Integration
export const getCarriers = () => api.get('/carriers');
export const getCarrierConfig = (carrierType) => api.get(`/carriers/${carrierType}`);
export const createCarrierConfig = (carrierType, credentials, testMode = true) =>
  api.post('/carriers', { carrier_type: carrierType, credentials, test_mode: testMode });
export const testCarrierConnection = (carrierType, credentials, testMode = true) =>
  api.post('/carriers/test-connection', { carrier_type: carrierType, credentials, test_mode: testMode });
export const toggleCarrierStatus = (carrierType) =>
  api.put(`/carriers/${carrierType}/toggle`);
export const deleteCarrierConfig = (carrierType) =>
  api.delete(`/carriers/${carrierType}`);

// AI Assistant
export const sendAIMessage = (message, model = 'gpt-4o', provider = 'openai', sessionId) =>
  api.post('/ai/message', { message, model, provider, session_id: sessionId });
export const getAIUsage = () => api.get('/ai/usage');

// WhatsApp
export const getWhatsAppConversations = (status = null, skip = 0, limit = 20) => 
  api.get('/whatsapp/conversations', { params: { status, skip, limit } });

export const getConversationMessages = (conversationId, limit = 50) => 
  api.get(`/whatsapp/conversation/${conversationId}/messages`, { params: { limit } });

export const sendWhatsAppMessage = (data) => api.post('/whatsapp/send', data);

export const sendOrderConfirmation = (orderId) => 
  api.post(`/whatsapp/send-order-confirmation/${orderId}`);

export const assignConversationToHuman = (conversationId) => 
  api.post(`/whatsapp/conversation/${conversationId}/assign`);

export const markConversationRead = (conversationId) => 
  api.post(`/whatsapp/conversation/${conversationId}/mark-read`);

// Shipping / Carrier Integration
export const shipOrder = (orderId, carrierType) => 
  api.post('/shipping/ship', { order_id: orderId, carrier_type: carrierType });

export const autoShipOrder = (orderId, strategy = 'priority') => 
  api.post('/shipping/auto-ship', { order_id: orderId, strategy });

export const bulkShipOrders = (orderIds, carrierType = 'auto', useSmartRouting = true) => 
  api.post('/shipping/bulk-ship', { 
    order_ids: orderIds, 
    carrier_type: carrierType,
    use_smart_routing: useSmartRouting
  });

export const smartBulkShip = (orderIds) => 
  api.post('/shipping/bulk-ship', { 
    order_ids: orderIds, 
    carrier_type: 'auto',
    use_smart_routing: true
  });

export const getShippingLabel = (orderId) => 
  api.get(`/shipping/label/${orderId}`, { responseType: 'blob' });

export const getBulkLabels = (orderIds) => 
  api.post('/shipping/bulk-labels', { order_ids: orderIds }, { responseType: 'blob' });

export const getCarrierTracking = (orderId) => 
  api.get(`/shipping/tracking/${orderId}`);

export const getActiveCarriers = () => 
  api.get('/shipping/active-carriers');

export const getCarrierStatus = (carrierType) =>
  api.get(`/shipping/carrier-status/${carrierType}`);

// Unified Tracking System - Control Tower
export const syncOrderStatus = (orderId, forceAdvance = false) =>
  api.post(`/shipping/sync-status/${orderId}`, { force_advance: forceAdvance });

export const bulkSyncStatus = (orderIds, forceAdvance = false) =>
  api.post('/shipping/bulk-sync-status', { order_ids: orderIds, force_advance: forceAdvance });

export const getOrderTimeline = (orderId) =>
  api.get(`/shipping/timeline/${orderId}`);

export default api;