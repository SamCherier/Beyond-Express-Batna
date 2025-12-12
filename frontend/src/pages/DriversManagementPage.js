import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Truck, UserPlus, Search, Edit, Trash2 } from 'lucide-react';
import api from '@/api';

const DriversManagementPage = () => {
  const { user } = useAuth();
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [newDriver, setNewDriver] = useState({
    name: '',
    email: '',
    password: '',
    phone: ''
  });

  useEffect(() => {
    fetchDrivers();
  }, []);

  const fetchDrivers = async () => {
    try {
      setLoading(true);
      // Get all users with role=delivery
      const response = await api.get('/users');
      const allUsers = response.data.users || response.data || [];
      // DEFENSIVE: Always ensure it's an array
      const safeUsers = Array.isArray(allUsers) ? allUsers : [];
      const driverUsers = safeUsers.filter(u => u.role === 'delivery');
      setDrivers(driverUsers);
    } catch (error) {
      console.error('Error fetching drivers:', error);
      toast.error('Erreur lors du chargement des chauffeurs');
      // ALWAYS set empty array, never undefined
      setDrivers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDriver = async () => {
    if (!newDriver.name || !newDriver.email || !newDriver.password) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      await api.post('/auth/register', {
        name: newDriver.name,
        email: newDriver.email,
        password: newDriver.password,
        role: 'delivery'
      });

      toast.success('Chauffeur créé avec succès');
      setDialogOpen(false);
      setNewDriver({ name: '', email: '', password: '', phone: '' });
      fetchDrivers();
    } catch (error) {
      console.error('Error creating driver:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors de la création';
      toast.error(errorMsg);
    }
  };

  const handleDeleteDriver = async (driverId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce chauffeur ?')) {
      return;
    }

    try {
      await api.delete(`/auth/users/${driverId}`);
      toast.success('Chauffeur supprimé');
      fetchDrivers();
    } catch (error) {
      console.error('Error deleting driver:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  // DEFENSIVE: Always ensure drivers is an array before filtering
  const filteredDrivers = (Array.isArray(drivers) ? drivers : []).filter(driver =>
    driver.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    driver.email?.toLowerCase().includes(searchQuery.toLowerCase())
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
            Gestion des Chauffeurs
          </h1>
          <p className="text-gray-600 mt-1">
            Gérez les livreurs et leurs accès à l'application mobile
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <UserPlus className="w-4 h-4" />
          Ajouter Chauffeur
        </Button>
      </div>

      {/* Stats Card */}
      <div className="bg-white p-6 rounded-lg border shadow-sm">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Truck className="w-8 h-8 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Total Chauffeurs</p>
            <p className="text-2xl font-bold text-gray-900">{drivers.length}</p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white p-4 rounded-lg border shadow-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Rechercher un chauffeur..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Drivers Table */}
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-4 text-left text-sm font-semibold text-gray-700">Nom</th>
                <th className="p-4 text-left text-sm font-semibold text-gray-700">Email</th>
                <th className="p-4 text-center text-sm font-semibold text-gray-700">Statut</th>
                <th className="p-4 text-center text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredDrivers.length === 0 ? (
                <tr>
                  <td colSpan="4" className="p-8 text-center text-gray-500">
                    Aucun chauffeur trouvé
                  </td>
                </tr>
              ) : (
                filteredDrivers.map(driver => (
                  <tr key={driver.id} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <Truck className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{driver.name}</p>
                          <p className="text-sm text-gray-500">ID: {driver.id?.substring(0, 8)}...</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4 text-gray-900">{driver.email}</td>
                    <td className="p-4 text-center">
                      <Badge variant="default" className="bg-green-600">
                        Actif
                      </Badge>
                    </td>
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteDriver(driver.id)}
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Driver Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter un Nouveau Chauffeur</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nom Complet *
              </label>
              <Input
                placeholder="Ex: Ahmed Benali"
                value={newDriver.name}
                onChange={(e) => setNewDriver({ ...newDriver, name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email *
              </label>
              <Input
                type="email"
                placeholder="ahmed.benali@beyond.com"
                value={newDriver.email}
                onChange={(e) => setNewDriver({ ...newDriver, email: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mot de Passe *
              </label>
              <Input
                type="password"
                placeholder="Minimum 8 caractères"
                value={newDriver.password}
                onChange={(e) => setNewDriver({ ...newDriver, password: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Téléphone (Optionnel)
              </label>
              <Input
                placeholder="0555123456"
                value={newDriver.phone}
                onChange={(e) => setNewDriver({ ...newDriver, phone: e.target.value })}
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                💡 <strong>Info:</strong> Le chauffeur pourra se connecter à l'application mobile avec cet email et mot de passe.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Annuler
            </Button>
            <Button onClick={handleCreateDriver}>
              <UserPlus className="w-4 h-4 mr-2" />
              Créer Chauffeur
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DriversManagementPage;
