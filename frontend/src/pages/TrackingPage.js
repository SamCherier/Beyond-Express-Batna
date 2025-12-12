import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Search, Package, Truck, CheckCircle, MapPin, Calendar, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import BeyondExpressLogo from '@/components/BeyondExpressLogo';
import api from '@/api';

const TrackingPage = () => {
  const { tracking_id } = useParams();
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState(tracking_id || '');
  const [trackingData, setTrackingData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (tracking_id) {
      fetchTrackingData(tracking_id);
    }
  }, [tracking_id]);

  const fetchTrackingData = async (id) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get(`/public/track/${id}`);
      setTrackingData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Numéro de suivi introuvable');
      setTrackingData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      navigate(`/tracking/${searchInput.trim()}`);
    }
  };

  const statusConfig = {
    in_stock: { label: 'En Stock', icon: Package, color: 'bg-blue-500', textColor: 'text-blue-600' },
    preparing: { label: 'En Préparation', icon: Package, color: 'bg-yellow-500', textColor: 'text-yellow-600' },
    ready_to_ship: { label: 'Prêt à Expédier', icon: Package, color: 'bg-purple-500', textColor: 'text-purple-600' },
    in_transit: { label: 'En Transit', icon: Truck, color: 'bg-orange-500', textColor: 'text-orange-600' },
    delivered: { label: 'Livré', icon: CheckCircle, color: 'bg-green-500', textColor: 'text-green-600' },
    returned: { label: 'Retourné', icon: Package, color: 'bg-red-500', textColor: 'text-red-600' },
    failed: { label: 'Échec', icon: AlertCircle, color: 'bg-gray-500', textColor: 'text-gray-600' }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-6 flex items-center justify-center">
          <BeyondExpressLogo size="md" />
          <h1 className="text-3xl font-bold ml-4" style={{ fontFamily: 'Hacen Tunisia, serif' }}>
            Beyond Express
          </h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Search Section */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-center mb-2" style={{ fontFamily: 'Hacen Tunisia, serif' }}>
            Suivez Votre Colis
          </h2>
          <p className="text-gray-600 text-center mb-6">
            Entrez votre numéro de suivi pour voir où se trouve votre commande
          </p>
          
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                type="text"
                placeholder="Entrez votre numéro de suivi (ex: TRK...)"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-12 py-6 text-lg"
              />
            </div>
            <Button 
              type="submit" 
              className="bg-red-500 hover:bg-red-600 px-8 py-6 text-lg"
              disabled={loading}
            >
              {loading ? 'Recherche...' : 'Suivre'}
            </Button>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-red-600" />
              <div>
                <p className="font-semibold text-red-900">Colis introuvable</p>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tracking Results */}
        {trackingData && (
          <div className="space-y-6">
            {/* Status Card */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              {/* Celebration Banner for Delivered */}
              {trackingData.status === 'delivered' && (
                <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white p-4 rounded-lg mb-6 text-center animate-pulse">
                  <p className="text-2xl font-bold">🎉 COLIS LIVRÉ AVEC SUCCÈS ! 🎉</p>
                </div>
              )}
              
              <div className="flex items-center justify-between mb-6">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Numéro de Suivi</p>
                  <p className="text-2xl font-bold font-mono">{trackingData.tracking_id}</p>
                </div>
                <div className={`px-6 py-3 rounded-full ${statusConfig[trackingData.status]?.color || 'bg-gray-500'} text-white font-bold flex items-center gap-2`}>
                  {React.createElement(statusConfig[trackingData.status]?.icon || Package, { className: 'w-5 h-5' })}
                  {statusConfig[trackingData.status]?.label || trackingData.status}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-6 border-t">
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Destination</p>
                    <p className="font-semibold">{trackingData.recipient_wilaya}</p>
                    {trackingData.recipient_commune && (
                      <p className="text-sm text-gray-600">{trackingData.recipient_commune}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-500">Date de Création</p>
                    <p className="font-semibold">{formatDate(trackingData.created_at)}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <h3 className="text-xl font-bold mb-6" style={{ fontFamily: 'Hacen Tunisia, serif' }}>
                Historique de Suivi
              </h3>
              
              {trackingData.events && trackingData.events.length > 0 ? (
                <div className="space-y-6">
                  {trackingData.events.map((event, index) => {
                    const config = statusConfig[event.status] || statusConfig.in_stock;
                    const Icon = config.icon;
                    const isLast = index === trackingData.events.length - 1;
                    
                    return (
                      <div key={index} className="flex gap-4">
                        {/* Timeline Line */}
                        <div className="flex flex-col items-center">
                          <div className={`w-12 h-12 rounded-full ${config.color} flex items-center justify-center text-white shadow-lg`}>
                            <Icon className="w-6 h-6" />
                          </div>
                          {!isLast && (
                            <div className="w-1 h-full bg-gray-200 mt-2" />
                          )}
                        </div>
                        
                        {/* Event Details */}
                        <div className="flex-1 pb-6">
                          <div className="flex items-center justify-between mb-2">
                            <p className={`font-bold text-lg ${config.textColor}`}>
                              {config.label}
                            </p>
                            <p className="text-sm text-gray-500">
                              {formatDate(event.timestamp)}
                            </p>
                          </div>
                          
                          {event.location && (
                            <p className="text-sm text-gray-600 flex items-center gap-2 mb-1">
                              <MapPin className="w-4 h-4" />
                              {event.location}
                            </p>
                          )}
                          
                          {event.notes && (
                            <p className="text-sm text-gray-600">{event.notes}</p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">Aucun événement de suivi disponible</p>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12 py-6">
        <div className="container mx-auto px-4 text-center text-gray-600">
          <p>© 2025 Beyond Express - Plateforme de Livraison Algérienne</p>
        </div>
      </footer>
    </div>
  );
};

export default TrackingPage;
