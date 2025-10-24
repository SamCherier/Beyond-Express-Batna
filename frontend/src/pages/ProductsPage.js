import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getProducts, createProduct, updateProductStock } from '@/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Plus, Search, ShoppingCart, Edit, Package2 } from 'lucide-react';
import { toast } from 'sonner';

const ProductsPage = () => {
  const { t } = useTranslation();
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editStockDialogOpen, setEditStockDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [newStock, setNewStock] = useState('');

  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    price: '',
    weight: '',
    category: ''
  });

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    filterProducts();
  }, [products, searchTerm]);

  const fetchProducts = async () => {
    try {
      const response = await getProducts();
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Erreur lors du chargement des produits');
    } finally {
      setLoading(false);
    }
  };

  const filterProducts = () => {
    let filtered = [...products];

    if (searchTerm) {
      filtered = filtered.filter(product => 
        product.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (product.category && product.category.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    setFilteredProducts(filtered);
  };

  const handleCreateProduct = async () => {
    try {
      const productData = {
        sku: formData.sku,
        name: formData.name,
        description: formData.description || null,
        price: parseFloat(formData.price),
        weight: formData.weight ? parseFloat(formData.weight) : null,
        category: formData.category || null
      };

      await createProduct(productData);
      toast.success('Produit créé avec succès!');
      setCreateDialogOpen(false);
      fetchProducts();
      resetForm();
    } catch (error) {
      console.error('Error creating product:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la création');
    }
  };

  const resetForm = () => {
    setFormData({
      sku: '',
      name: '',
      description: '',
      price: '',
      weight: '',
      category: ''
    });
  };

  const handleUpdateStock = async () => {
    if (!selectedProduct || !newStock) return;

    try {
      await updateProductStock(selectedProduct.id, parseInt(newStock));
      toast.success('Stock mis à jour!');
      setEditStockDialogOpen(false);
      setSelectedProduct(null);
      setNewStock('');
      fetchProducts();
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du stock');
    }
  };

  const openEditStockDialog = (product) => {
    setSelectedProduct(product);
    setNewStock(product.stock_available.toString());
    setEditStockDialogOpen(true);
  };

  const getStockStatus = (available, reserved) => {
    const total = available + reserved;
    if (total === 0) return { label: 'Rupture', color: 'bg-red-100 text-red-700' };
    if (available < 10) return { label: 'Stock faible', color: 'bg-yellow-100 text-yellow-700' };
    return { label: 'En stock', color: 'bg-green-100 text-green-700' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="products-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>
            {t('products')}
          </h1>
          <p className="text-gray-600 mt-1">Gérez votre catalogue de produits</p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-red-500 hover:bg-red-600" data-testid="create-product-button">
              <Plus className="w-4 h-4 mr-2" />
              {t('createProduct')}
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Ajouter un nouveau produit</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4 py-4">
              <div className="space-y-2">
                <Label>SKU *</Label>
                <Input
                  value={formData.sku}
                  onChange={(e) => setFormData({...formData, sku: e.target.value})}
                  placeholder="SKU-001"
                  data-testid="sku-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Nom du produit *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Nom"
                  data-testid="product-name-input"
                />
              </div>
              <div className="col-span-2 space-y-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Description du produit"
                  data-testid="description-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Prix (DA) *</Label>
                <Input
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData({...formData, price: e.target.value})}
                  placeholder="0.00"
                  data-testid="price-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Poids (kg)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.weight}
                  onChange={(e) => setFormData({...formData, weight: e.target.value})}
                  placeholder="0.0"
                  data-testid="weight-input"
                />
              </div>
              <div className="col-span-2 space-y-2">
                <Label>Catégorie</Label>
                <Input
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                  placeholder="Électronique, Vêtements, etc."
                  data-testid="category-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Annuler</Button>
              <Button onClick={handleCreateProduct} className="bg-red-500 hover:bg-red-600" data-testid="submit-product-button">
                Ajouter le produit
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
              placeholder="Rechercher par SKU, nom ou catégorie..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
              data-testid="search-input"
            />
          </div>
        </CardContent>
      </Card>

      {/* Products Grid */}
      {filteredProducts.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <ShoppingCart className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Aucun produit trouvé</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProducts.map((product) => {
            const stockStatus = getStockStatus(product.stock_available, product.stock_reserved);
            return (
              <Card key={product.id} className="hover:shadow-lg transition-shadow" data-testid={`product-card-${product.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-red-50 to-orange-50 rounded-xl flex items-center justify-center">
                      <Package2 className="w-6 h-6 text-red-500" />
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${stockStatus.color}`}>
                      {stockStatus.label}
                    </span>
                  </div>
                  
                  <div className="space-y-2 mb-4">
                    <h3 className="text-lg font-bold text-gray-900">{product.name}</h3>
                    <p className="text-sm text-gray-500 font-mono">{product.sku}</p>
                    {product.description && (
                      <p className="text-sm text-gray-600 line-clamp-2">{product.description}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4 py-4 border-y border-gray-100">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Prix</p>
                      <p className="text-lg font-bold text-gray-900">{product.price} DA</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Stock disponible</p>
                      <p className="text-lg font-bold text-green-600">{product.stock_available}</p>
                    </div>
                  </div>

                  {product.stock_reserved > 0 && (
                    <div className="mb-4">
                      <p className="text-xs text-gray-500">Stock réservé</p>
                      <p className="text-sm font-medium text-orange-600">{product.stock_reserved} unités</p>
                    </div>
                  )}

                  {product.category && (
                    <div className="mb-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {product.category}
                      </span>
                    </div>
                  )}

                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => openEditStockDialog(product)}
                    data-testid={`edit-stock-${product.id}`}
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Modifier le stock
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Edit Stock Dialog */}
      <Dialog open={editStockDialogOpen} onOpenChange={setEditStockDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier le stock</DialogTitle>
          </DialogHeader>
          {selectedProduct && (
            <div className="py-4">
              <div className="mb-4">
                <p className="text-sm text-gray-500">Produit</p>
                <p className="font-medium">{selectedProduct.name}</p>
                <p className="text-sm text-gray-500 font-mono">{selectedProduct.sku}</p>
              </div>
              <div className="space-y-2">
                <Label>Stock disponible</Label>
                <Input
                  type="number"
                  value={newStock}
                  onChange={(e) => setNewStock(e.target.value)}
                  placeholder="Quantité"
                  data-testid="new-stock-input"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditStockDialogOpen(false)}>Annuler</Button>
            <Button onClick={handleUpdateStock} className="bg-red-500 hover:bg-red-600" data-testid="update-stock-button">
              Mettre à jour
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProductsPage;