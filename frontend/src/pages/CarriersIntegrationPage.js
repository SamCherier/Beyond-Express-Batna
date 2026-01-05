import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import api, {
  getCarriers,
  createCarrierConfig,
  testCarrierConnection,
  toggleCarrierStatus,
  deleteCarrierConfig
} from '@/api';
import {
  Check,
  X,
  Settings,
  Loader2,
  AlertCircle,
  CheckCircle,
  XCircle,
  Wifi,
  WifiOff,
  Trash2,
  Plus,
  Truck,
  Globe
} from 'lucide-react';
import { toast } from 'sonner';

const CarriersIntegrationPage = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  
  const [carriers, setCarriers] = useState([]);
  const [genericCarriers, setGenericCarriers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCarrier, setSelectedCarrier] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showGenericModal, setShowGenericModal] = useState(false);
  const [credentials, setCredentials] = useState({});
  const [testMode, setTestMode] = useState(true);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saveLoading, setSaveLoading] = useState(false);
  
  // Generic carrier form state
  const [genericForm, setGenericForm] = useState({
    name: '',
    base_url: '',
    auth_type: 'bearer',
    auth_header_name: 'Authorization',
    auth_header_template: 'Bearer {KEY}',
    api_key: '',
    secret_key: '',
    logo_color: '#1E3A8A'
  });

  useEffect(() => {
    fetchCarriers();
    if (isAdmin) {
      fetchGenericCarriers();
    }
  }, [isAdmin]);

  const fetchCarriers = async () => {
    try {
      setLoading(true);
      const response = await getCarriers();
      console.log('✅ Carriers loaded:', response.data);
      
      // Add Anderson to the list if not present
      const carriersList = response.data;
      const hasAnderson = carriersList.some(c => c.carrier_type === 'anderson');
      
      if (!hasAnderson) {
        carriersList.push({
          carrier_type: 'anderson',
          name: 'Anderson Logistics',
          description: 'Service logistique premium - Couverture nationale Algérie',
          is_configured: false,
          is_active: false,
          required_fields: ['api_key', 'secret_key'],
          logo_color: '#1E3A8A'
        });
      }
      
      setCarriers(carriersList);
    } catch (error) {
      console.error('❌ Error fetching carriers:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors du chargement des transporteurs';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchGenericCarriers = async () => {
    try {
      const response = await api.get('/carriers/generic');
      setGenericCarriers(response.data.carriers || []);
    } catch (error) {
      console.error('Error fetching generic carriers:', error);
    }
  };

  const openConfigModal = (carrier) => {
    setSelectedCarrier(carrier);
    setCredentials({});
    setTestResult(null);
    setShowConfigModal(true);
  };

  const closeConfigModal = () => {
    setShowConfigModal(false);
    setSelectedCarrier(null);
    setCredentials({});
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    if (!selectedCarrier) return;

    setTestLoading(true);
    setTestResult(null);

    try {
      const response = await testCarrierConnection(
        selectedCarrier.carrier_type,
        credentials,
        testMode
      );

      setTestResult({
        success: response.data.success,
        message: response.data.message,
        response_time_ms: response.data.response_time_ms
      });

      if (response.data.success) {
        toast.success('Test de connexion réussi!');
      } else {
        toast.error('Échec du test de connexion');
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors du test de connexion';
      setTestResult({
        success: false,
        message: errorMsg
      });
      toast.error(errorMsg);
    } finally {
      setTestLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!selectedCarrier) return;

    if (!testResult || !testResult.success) {
      toast.error('Veuillez tester la connexion avant de sauvegarder');
      return;
    }

    setSaveLoading(true);

    try {
      await createCarrierConfig(selectedCarrier.carrier_type, credentials, testMode);
      toast.success('Configuration sauvegardée avec succès!');
      closeConfigModal();
      fetchCarriers();
    } catch (error) {
      console.error('Error saving config:', error);
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleToggleCarrier = async (carrier) => {
    if (!carrier.is_configured) {
      toast.error('Veuillez d\'abord configurer ce transporteur');
      return;
    }

    try {
      const response = await toggleCarrierStatus(carrier.carrier_type);
      toast.success(response.data.message);
      fetchCarriers();
    } catch (error) {
      console.error('Error toggling carrier:', error);
      toast.error('Erreur lors de l\'activation/désactivation');
    }
  };

  const handleDeleteConfig = async (carrier) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette configuration?')) {
      return;
    }

    try {
      await deleteCarrierConfig(carrier.carrier_type);
      toast.success('Configuration supprimée');
      fetchCarriers();
    } catch (error) {
      console.error('Error deleting config:', error);
      toast.error('Erreur lors de la suppression');
    }
  };
  
  // Generic Carrier Functions
  const handleCreateGenericCarrier = async () => {
    if (!genericForm.name || !genericForm.base_url) {
      toast.error('Nom et URL de base requis');
      return;
    }
    
    setSaveLoading(true);
    try {
      await api.post('/carriers/generic', genericForm);
      toast.success(`${genericForm.name} ajouté avec succès!`);
      setShowGenericModal(false);
      setGenericForm({
        name: '',
        base_url: '',
        auth_type: 'bearer',
        auth_header_name: 'Authorization',
        auth_header_template: 'Bearer {KEY}',
        api_key: '',
        secret_key: '',
        logo_color: '#1E3A8A'
      });
      fetchGenericCarriers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création');
    } finally {
      setSaveLoading(false);
    }
  };
  
  const handleDeleteGenericCarrier = async (carrierId) => {
    if (!window.confirm('Supprimer ce transporteur personnalisé?')) return;
    
    try {
      await api.delete(`/carriers/generic/${carrierId}`);
      toast.success('Transporteur supprimé');
      fetchGenericCarriers();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const getStatusBadge = (carrier) => {
    if (!carrier.is_configured) {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600">
          <WifiOff className="w-3 h-3" />
          Non configuré
        </span>
      );
    }

    if (carrier.is_active) {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
          <CheckCircle className="w-3 h-3" />
          Actif
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-700">
        <Wifi className="w-3 h-3" />
        Configuré
      </span>
    );
  };

  const renderCredentialFields = () => {
    if (!selectedCarrier) return null;

    const fields = selectedCarrier.required_fields || [];

    return fields.map((field) => {
      const fieldLabels = {
        api_key: 'Clé API (API Key)',
        api_token: 'Token API',
        user_id: 'User ID',
        center_id: 'Center ID',
        api_secret: 'API Secret'
      };

      return (
        <div key={field} className="space-y-2">
          <Label htmlFor={field} className="text-sm font-semibold text-gray-700">
            {fieldLabels[field] || field} *
          </Label>
          <Input
            id={field}
            type="password"
            value={credentials[field] || ''}
            onChange={(e) => setCredentials({ ...credentials, [field]: e.target.value })}
            placeholder={`Entrez votre ${fieldLabels[field] || field}`}
            className="font-mono text-sm"
          />
        </div>
      );
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-red-500" />
      </div>
    );
  }

  return (
    <div className="p-8 font-hacen" style={{ fontFamily: 'Hacen Tunisia Bd, sans-serif' }}>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Intégrations Transporteurs
        </h1>
        <p className="text-gray-600">
          Connectez vos comptes API pour envoyer automatiquement vos commandes aux transporteurs
        </p>
      </div>

      {/* Carriers Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {carriers.map((carrier) => (
          <div
            key={carrier.carrier_type}
            className="relative bg-white rounded-xl shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow"
          >
            {/* Logo */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: carrier.logo_color ? `${carrier.logo_color}20` : '#f3f4f6' }}
                >
                  {carrier.carrier_type === 'anderson' ? (
                    <span 
                      className="text-xl font-black"
                      style={{ color: carrier.logo_color || '#1E3A8A' }}
                    >
                      A
                    </span>
                  ) : (
                    <Truck 
                      className="w-6 h-6"
                      style={{ color: carrier.logo_color || '#6b7280' }}
                    />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    {carrier.name}
                  </h3>
                  {getStatusBadge(carrier)}
                </div>
              </div>
            </div>

            {/* Description */}
            <p className="text-sm text-gray-600 mb-4">
              {carrier.description}
            </p>

            {/* Toggle Switch (only if configured) */}
            {carrier.is_configured && (
              <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-semibold text-gray-700">
                  {carrier.is_active ? 'Activé' : 'Désactivé'}
                </span>
                <button
                  onClick={() => handleToggleCarrier(carrier)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    carrier.is_active ? 'bg-green-500' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      carrier.is_active ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                onClick={() => openConfigModal(carrier)}
                className="flex-1 bg-red-500 hover:bg-red-600 text-white"
              >
                <Settings className="w-4 h-4 mr-2" />
                {carrier.is_configured ? 'Reconfigurer' : 'Configurer'}
              </Button>

              {carrier.is_configured && (
                <Button
                  onClick={() => handleDeleteConfig(carrier)}
                  variant="outline"
                  className="border-red-200 text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        ))}
        
        {/* Generic/Custom Carriers (Admin Only) */}
        {isAdmin && genericCarriers.map((carrier) => (
          <div
            key={carrier.carrier_id}
            className="relative bg-white rounded-xl shadow-md border-2 border-dashed border-purple-300 p-6 hover:shadow-lg transition-shadow"
          >
            <div className="absolute -top-2 -right-2 px-2 py-1 bg-purple-500 text-white text-xs rounded-full">
              Custom
            </div>
            
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${carrier.logo_color}20` }}
                >
                  <Globe 
                    className="w-6 h-6"
                    style={{ color: carrier.logo_color }}
                  />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    {carrier.name}
                  </h3>
                  <span className="text-xs text-purple-600 font-mono">
                    {carrier.base_url?.substring(0, 30)}...
                  </span>
                </div>
              </div>
            </div>

            <p className="text-sm text-gray-600 mb-4">
              API personnalisée - Configurée par Admin
            </p>

            <div className="flex gap-2">
              <Button
                onClick={() => handleDeleteGenericCarrier(carrier.carrier_id)}
                variant="outline"
                className="flex-1 border-red-200 text-red-600 hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Supprimer
              </Button>
            </div>
          </div>
        ))}
      </div>
      
      {/* Add Custom API Button (ADMIN ONLY) */}
      {isAdmin && (
        <div className="mt-8 border-t border-gray-200 pt-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">API Personnalisée</h2>
              <p className="text-sm text-gray-600">Ajoutez des transporteurs inconnus sans coder</p>
            </div>
            <Button
              onClick={() => setShowGenericModal(true)}
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              <Plus className="w-4 h-4 mr-2" />
              Ajouter API Personnalisée
            </Button>
          </div>
        </div>
      )}

      {/* Configuration Modal */}
      {showConfigModal && selectedCarrier && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={closeConfigModal}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 rounded-t-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Configuration {selectedCarrier.name}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Entrez vos clés API pour connecter votre compte
                  </p>
                </div>
                <button
                  onClick={closeConfigModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {/* Test Mode Toggle */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-blue-900">Mode Test (Sandbox)</p>
                    <p className="text-sm text-blue-700">
                      Utilisez les clés de test pour développer sans créer de vraies commandes
                    </p>
                  </div>
                  <button
                    onClick={() => setTestMode(!testMode)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      testMode ? 'bg-blue-500' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        testMode ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Credential Fields */}
              <div className="space-y-4">
                {renderCredentialFields()}
              </div>

              {/* Test Result */}
              {testResult && (
                <div
                  className={`p-4 rounded-lg border ${
                    testResult.success
                      ? 'bg-green-50 border-green-200'
                      : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {testResult.success ? (
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p
                        className={`font-semibold ${
                          testResult.success ? 'text-green-900' : 'text-red-900'
                        }`}
                      >
                        {testResult.success ? 'Test réussi!' : 'Test échoué'}
                      </p>
                      <p
                        className={`text-sm ${
                          testResult.success ? 'text-green-700' : 'text-red-700'
                        }`}
                      >
                        {testResult.message}
                      </p>
                      {testResult.response_time_ms && (
                        <p className="text-xs text-gray-600 mt-1">
                          Temps de réponse: {testResult.response_time_ms.toFixed(0)} ms
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 p-6 rounded-b-2xl">
              <div className="flex gap-3">
                <Button
                  onClick={handleTestConnection}
                  disabled={testLoading}
                  variant="outline"
                  className="flex-1 border-blue-300 text-blue-600 hover:bg-blue-50"
                >
                  {testLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Wifi className="w-4 h-4 mr-2" />
                  )}
                  Tester la connexion
                </Button>

                <Button
                  onClick={handleSaveConfig}
                  disabled={saveLoading || !testResult?.success}
                  className="flex-1 bg-green-500 hover:bg-green-600 text-white"
                >
                  {saveLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4 mr-2" />
                  )}
                  Sauvegarder
                </Button>
              </div>

              {!testResult?.success && testResult && (
                <p className="text-sm text-center text-gray-600 mt-3">
                  ⚠️ Testez d'abord la connexion avant de sauvegarder
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CarriersIntegrationPage;
