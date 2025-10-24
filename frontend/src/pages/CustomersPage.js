import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getCustomers, createCustomer } from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, Search, Users, Mail, Phone, MapPin, ShoppingBag } from 'lucide-react';
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

const CustomersPage = () => {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState([]);
  const [filteredCustomers, setFilteredCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    address: '',
    wilaya: '',
    commune: '',
    notes: ''
  });

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    filterCustomers();
  }, [customers, searchTerm]);

  const fetchCustomers = async () => {
    try {
      const response = await getCustomers();
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
      toast.error('Erreur lors du chargement des clients');
    } finally {
      setLoading(false);
    }
  };

  const filterCustomers = () => {
    let filtered = [...customers];

    if (searchTerm) {
      filtered = filtered.filter(customer => 
        customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        customer.phone.toLowerCase().includes(searchTerm.toLowerCase()) ||
        customer.wilaya.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredCustomers(filtered);
  };

  const handleCreateCustomer = async () => {
    try {
      const customerData = {
        name: formData.name,
        phone: formData.phone,
        address: formData.address,
        wilaya: formData.wilaya,
        commune: formData.commune,
        notes: formData.notes || null
      };

      await createCustomer(customerData);
      toast.success('Client ajouté avec succès!');
      setCreateDialogOpen(false);
      fetchCustomers();
      resetForm();
    } catch (error) {
      console.error('Error creating customer:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'ajout');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      phone: '',
      address: '',
      wilaya: '',
      commune: '',
      notes: ''
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="customers-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>
            {t('customers')}
          </h1>
          <p className="text-gray-600 mt-1">Gérez votre base de données clients</p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-red-500 hover:bg-red-600" data-testid="create-customer-button">
              <Plus className="w-4 h-4 mr-2" />
              Ajouter un client
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Ajouter un nouveau client</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4 py-4">
              <div className="space-y-2">
                <Label>Nom complet *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Nom du client"
                  data-testid="customer-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Téléphone *</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  placeholder="0555123456"
                  data-testid="customer-phone-input"
                />
              </div>
              <div className="col-span-2 space-y-2">
                <Label>Adresse *</Label>
                <Input
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  placeholder="Adresse complète"
                  data-testid="customer-address-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Wilaya *</Label>
                <Select value={formData.wilaya} onValueChange={(val) => setFormData({...formData, wilaya: val})}>
                  <SelectTrigger data-testid="customer-wilaya-select">
                    <SelectValue placeholder="Sélectionner" />
                  </SelectTrigger>
                  <SelectContent>
                    {ALGERIAN_WILAYAS.map(w => (
                      <SelectItem key={w} value={w}>{w}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Commune *</Label>
                <Input
                  value={formData.commune}
                  onChange={(e) => setFormData({...formData, commune: e.target.value})}
                  placeholder="Commune"
                  data-testid="customer-commune-input"
                />
              </div>
              <div className="col-span-2 space-y-2">
                <Label>Notes</Label>
                <Input
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  placeholder="Informations supplémentaires"
                  data-testid="customer-notes-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Annuler</Button>
              <Button onClick={handleCreateCustomer} className="bg-red-500 hover:bg-red-600" data-testid="submit-customer-button">
                Ajouter le client
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Rechercher par nom, téléphone ou wilaya..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
              data-testid="search-input"
            />
          </div>
        </CardContent>
      </Card>

      {/* Customers Grid */}
      {filteredCustomers.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Users className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Aucun client trouvé</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCustomers.map((customer) => (
            <Card key={customer.id} className="hover:shadow-lg transition-shadow" data-testid={`customer-card-${customer.id}`}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-50 to-blue-50 rounded-full flex items-center justify-center">
                    <span className="text-xl font-bold text-purple-600">
                      {customer.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  {customer.order_count > 0 && (
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                      {customer.order_count} commandes
                    </span>
                  )}
                </div>
                
                <div className="space-y-3">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-1">{customer.name}</h3>
                  </div>

                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span>{customer.phone}</span>
                  </div>

                  <div className="flex items-start gap-2 text-sm text-gray-600">
                    <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
                    <div>
                      <p>{customer.address}</p>
                      <p className="font-medium text-gray-900">{customer.commune}, {customer.wilaya}</p>
                    </div>
                  </div>

                  {customer.notes && (
                    <div className="pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-500 mb-1">Notes</p>
                      <p className="text-sm text-gray-700">{customer.notes}</p>
                    </div>
                  )}

                  <div className="pt-3 border-t border-gray-100">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Client depuis</span>
                      <span>{new Date(customer.created_at).toLocaleDateString('fr-FR')}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                  <Button variant="outline" className="flex-1" size="sm">
                    <ShoppingBag className="w-4 h-4 mr-2" />
                    Commandes
                  </Button>
                  <Button variant="outline" size="sm">
                    <Mail className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default CustomersPage;