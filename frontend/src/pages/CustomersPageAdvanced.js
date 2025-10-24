import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getCustomers, createCustomer, updateCustomer, generateCustomerQR, uploadProfilePicture } from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, Search, Users, Mail, Phone, MapPin, ShoppingBag, QrCode, Facebook, Instagram, Edit, Upload } from 'lucide-react';
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

const CustomersPageAdvanced = () => {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState([]);
  const [filteredCustomers, setFilteredCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [qrDialogOpen, setQrDialogOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [qrImage, setQrImage] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    phone2: '',
    address: '',
    wilaya: '',
    commune: '',
    notes: '',
    facebook_url: '',
    instagram_url: '',
    profile_picture: ''
  });

  const [uploadingImage, setUploadingImage] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);

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
        customer.wilaya.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (customer.customer_id && customer.customer_id.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    setFilteredCustomers(filtered);
  };

  const handleCreateCustomer = async () => {
    try {
      const customerData = {
        name: formData.name,
        phone: formData.phone,
        phone2: formData.phone2 || null,
        address: formData.address,
        wilaya: formData.wilaya,
        commune: formData.commune,
        notes: formData.notes || null,
        facebook_url: formData.facebook_url || null,
        instagram_url: formData.instagram_url || null,
        profile_picture: formData.profile_picture || null
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
      phone2: '',
      address: '',
      wilaya: '',
      commune: '',
      notes: '',
      facebook_url: '',
      instagram_url: '',
      profile_picture: ''
    });
    setPreviewImage(null);
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Le fichier doit être une image (JPG, PNG)');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('La taille de l\'image ne doit pas dépasser 5MB');
      return;
    }

    setUploadingImage(true);
    try {
      const response = await uploadProfilePicture(file);
      const imageUrl = `${process.env.REACT_APP_BACKEND_URL}${response.data.url}`;
      setFormData({...formData, profile_picture: imageUrl});
      setPreviewImage(imageUrl);
      toast.success('Image uploadée avec succès!');
    } catch (error) {
      console.error('Error uploading image:', error);
      toast.error('Erreur lors de l\'upload de l\'image');
    } finally {
      setUploadingImage(false);
    }
  };

  const handleGenerateQR = async (customer) => {
    try {
      const response = await generateCustomerQR(customer.id);
      const blob = new Blob([response.data], { type: 'image/png' });
      const imageUrl = URL.createObjectURL(blob);
      setQrImage(imageUrl);
      setSelectedCustomer(customer);
      setQrDialogOpen(true);
    } catch (error) {
      toast.error('Erreur lors de la génération du QR code');
    }
  };

  const downloadQR = () => {
    if (qrImage && selectedCustomer) {
      const link = document.createElement('a');
      link.href = qrImage;
      link.download = `qr_${selectedCustomer.customer_id}.png`;
      link.click();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="customers-advanced-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>
            {t('customers')} CRM
          </h1>
          <p className="text-gray-600 mt-1">Gestion avancée de votre base clients</p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-red-500 hover:bg-red-600" data-testid="create-customer-button">
              <Plus className="w-4 h-4 mr-2" />
              Ajouter un client
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Ajouter un nouveau client</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4 py-4">
              <div className="col-span-2 space-y-2">
                <Label>Photo de profil (URL)</Label>
                <Input
                  value={formData.profile_picture}
                  onChange={(e) => setFormData({...formData, profile_picture: e.target.value})}
                  placeholder="https://example.com/photo.jpg"
                  data-testid="profile-picture-input"
                />
              </div>
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
                <Label>Téléphone principal *</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  placeholder="0555123456"
                  data-testid="customer-phone-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Téléphone secondaire</Label>
                <Input
                  value={formData.phone2}
                  onChange={(e) => setFormData({...formData, phone2: e.target.value})}
                  placeholder="0666123456"
                  data-testid="customer-phone2-input"
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
                  value={formData.commune}
                  onChange={(e) => setFormData({...formData, commune: e.target.value})}
                  placeholder="Commune"
                  data-testid="customer-commune-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Facebook (URL)</Label>
                <Input
                  value={formData.facebook_url}
                  onChange={(e) => setFormData({...formData, facebook_url: e.target.value})}
                  placeholder="https://facebook.com/..."
                  data-testid="facebook-url-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Instagram (URL)</Label>
                <Input
                  value={formData.instagram_url}
                  onChange={(e) => setFormData({...formData, instagram_url: e.target.value})}
                  placeholder="https://instagram.com/..."
                  data-testid="instagram-url-input"
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
              placeholder="Rechercher par ID, nom, téléphone ou wilaya..."
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
            <Card key={customer.id} className="hover:shadow-xl transition-all" data-testid={`customer-card-${customer.id}`}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  {customer.profile_picture ? (
                    <img src={customer.profile_picture} alt={customer.name} className="w-16 h-16 rounded-full object-cover" />
                  ) : (
                    <div className="w-16 h-16 bg-gradient-to-br from-purple-50 to-blue-50 rounded-full flex items-center justify-center">
                      <span className="text-2xl font-bold text-purple-600">
                        {customer.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                  <div className="flex flex-col gap-1">
                    <span className="px-3 py-1 rounded-full text-xs font-mono bg-blue-100 text-blue-700">
                      {customer.customer_id || 'N/A'}
                    </span>
                    {customer.order_count > 0 && (
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        {customer.order_count} cmd
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-1">{customer.name}</h3>
                  </div>

                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span>{customer.phone}</span>
                  </div>

                  {customer.phone2 && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Phone className="w-4 h-4 text-gray-400" />
                      <span>{customer.phone2}</span>
                    </div>
                  )}

                  <div className="flex items-start gap-2 text-sm text-gray-600">
                    <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
                    <div>
                      <p>{customer.address}</p>
                      <p className="font-medium text-gray-900">{customer.commune}, {customer.wilaya}</p>
                    </div>
                  </div>

                  {(customer.facebook_url || customer.instagram_url) && (
                    <div className="flex gap-2 pt-2">
                      {customer.facebook_url && (
                        <a href={customer.facebook_url} target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg bg-blue-50 hover:bg-blue-100 transition-colors">
                          <Facebook className="w-4 h-4 text-blue-600" />
                        </a>
                      )}
                      {customer.instagram_url && (
                        <a href={customer.instagram_url} target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg bg-pink-50 hover:bg-pink-100 transition-colors">
                          <Instagram className="w-4 h-4 text-pink-600" />
                        </a>
                      )}
                    </div>
                  )}

                  {customer.notes && (
                    <div className="pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-500 mb-1">Notes</p>
                      <p className="text-sm text-gray-700">{customer.notes}</p>
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                  <Button 
                    variant="outline" 
                    className="flex-1" 
                    size="sm"
                    onClick={() => handleGenerateQR(customer)}
                    data-testid={`generate-qr-${customer.id}`}
                  >
                    <QrCode className="w-4 h-4 mr-2" />
                    QR Code
                  </Button>
                  <Button variant="outline" size="sm">
                    <ShoppingBag className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* QR Code Dialog */}
      <Dialog open={qrDialogOpen} onOpenChange={setQrDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>QR Code Client</DialogTitle>
          </DialogHeader>
          {selectedCustomer && (
            <div className="py-4 space-y-4">
              <div className="text-center">
                <p className="text-sm text-gray-500 mb-2">ID Client</p>
                <p className="font-mono font-bold text-lg">{selectedCustomer.customer_id}</p>
                <p className="font-medium">{selectedCustomer.name}</p>
                <p className="text-sm text-gray-600">{selectedCustomer.phone}</p>
              </div>
              {qrImage && (
                <div className="flex justify-center bg-white p-4 rounded-lg border-2 border-gray-200">
                  <img src={qrImage} alt="QR Code" className="w-64 h-64" />
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setQrDialogOpen(false)}>Fermer</Button>
            <Button onClick={downloadQR} className="bg-red-500 hover:bg-red-600">
              Télécharger QR
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CustomersPageAdvanced;
