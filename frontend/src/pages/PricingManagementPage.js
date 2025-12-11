import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Edit, Save, X, MapPin, Home, Building2 } from 'lucide-react';
import api from '@/api';

const PricingManagementPage = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [pricing, setPricing] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingWilaya, setEditingWilaya] = useState(null);
  const [editedPrices, setEditedPrices] = useState({ home: 0, desk: 0 });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchPricing();
  }, []);

  const fetchPricing = async () => {
    try {
      setLoading(true);
      const response = await api.get('/pricing/');
      
      // Group by wilaya
      const grouped = {};
      response.data.pricing.forEach(item => {
        if (!grouped[item.wilaya]) {
          grouped[item.wilaya] = { wilaya: item.wilaya, home: 0, desk: 0 };
        }
        if (item.delivery_type === 'home') {
          grouped[item.wilaya].home = item.price;
          grouped[item.wilaya].homeId = item.id;
        } else if (item.delivery_type === 'desk') {
          grouped[item.wilaya].desk = item.price;
          grouped[item.wilaya].deskId = item.id;
        }
      });

      setPricing(Object.values(grouped).sort((a, b) => a.wilaya.localeCompare(b.wilaya)));
    } catch (error) {
      console.error('Error fetching pricing:', error);
      toast.error('Erreur lors du chargement des tarifs');
    } finally {
      setLoading(false);
    }
  };

  const handleEditWilaya = (wilayaData) => {
    setEditingWilaya(wilayaData.wilaya);
    setEditedPrices({ home: wilayaData.home, desk: wilayaData.desk });
  };

  const handleSavePricing = async () => {
    try {
      // Update home pricing
      await api.post('/pricing/', {
        wilaya: editingWilaya,
        delivery_type: 'home',
        price: parseFloat(editedPrices.home)
      });

      // Update desk pricing
      await api.post('/pricing/', {
        wilaya: editingWilaya,
        delivery_type: 'desk',
        price: parseFloat(editedPrices.desk)
      });

      toast.success('Tarifs mis à jour avec succès');
      setEditingWilaya(null);
      fetchPricing();
    } catch (error) {
      console.error('Error updating pricing:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const filteredPricing = pricing.filter(item =>
    item.wilaya.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Hacen Tunisia, serif' }}>
            Gestion des Tarifs de Livraison
          </h1>
          <p className="text-gray-600 mt-1">
            Configurez les prix par wilaya pour les livraisons à domicile et stop desk
          </p>
        </div>
        <Badge variant="secondary" className="text-base px-4 py-2">
          <MapPin className="w-4 h-4 mr-2" />
          {pricing.length} Wilayas configurées
        </Badge>
      </div>

      {/* Search */}
      <div className="bg-white p-4 rounded-lg border shadow-sm">
        <Input
          placeholder="Rechercher une wilaya..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-md"
        />
      </div>

      {/* Pricing Table */}
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-4 text-left text-sm font-semibold text-gray-700">Wilaya</th>
                <th className="p-4 text-center text-sm font-semibold text-gray-700">
                  <div className="flex items-center justify-center gap-2">
                    <Home className="w-4 h-4" />
                    Prix Domicile (DZD)
                  </div>
                </th>
                <th className="p-4 text-center text-sm font-semibold text-gray-700">
                  <div className="flex items-center justify-center gap-2">
                    <Building2 className="w-4 h-4" />
                    Prix Stop Desk (DZD)
                  </div>
                </th>
                <th className="p-4 text-center text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredPricing.length === 0 ? (
                <tr>
                  <td colSpan="4" className="p-8 text-center text-gray-500">
                    Aucune wilaya trouvée
                  </td>
                </tr>
              ) : (
                filteredPricing.map(item => (
                  <tr key={item.wilaya} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-gray-400" />
                        <span className="font-medium text-gray-900">{item.wilaya}</span>
                      </div>
                    </td>
                    <td className="p-4 text-center">
                      <span className="inline-flex items-center px-3 py-1 rounded-full bg-green-50 text-green-700 font-semibold">
                        {item.home.toFixed(2)} DZD
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <span className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-blue-700 font-semibold">
                        {item.desk.toFixed(2)} DZD
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditWilaya(item)}
                        className="gap-2"
                      >
                        <Edit className="w-4 h-4" />
                        Modifier
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={!!editingWilaya} onOpenChange={(open) => !open && setEditingWilaya(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier les tarifs - {editingWilaya}</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <div className="flex items-center gap-2">
                  <Home className="w-4 h-4" />
                  Prix Livraison à Domicile (DZD)
                </div>
              </label>
              <Input
                type="number"
                step="0.01"
                value={editedPrices.home}
                onChange={(e) => setEditedPrices({ ...editedPrices, home: e.target.value })}
                placeholder="400.00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4" />
                  Prix Livraison Stop Desk (DZD)
                </div>
              </label>
              <Input
                type="number"
                step="0.01"
                value={editedPrices.desk}
                onChange={(e) => setEditedPrices({ ...editedPrices, desk: e.target.value })}
                placeholder="350.00"
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                💡 <strong>Astuce :</strong> Les prix Stop Desk sont généralement 50 DZD moins chers que les prix à domicile.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingWilaya(null)}>
              <X className="w-4 h-4 mr-2" />
              Annuler
            </Button>
            <Button onClick={handleSavePricing}>
              <Save className="w-4 h-4 mr-2" />
              Enregistrer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PricingManagementPage;
