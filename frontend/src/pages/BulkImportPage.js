import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { 
  Upload, 
  Download, 
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Package
} from 'lucide-react';
import api from '@/api';

const BulkImportPage = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.get('/orders/template', {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'template_import_commandes.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Modèle téléchargé avec succès');
    } catch (error) {
      console.error('Error downloading template:', error);
      toast.error('Erreur lors du téléchargement du modèle');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile) => {
    // Validate file type
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'text/csv'
    ];
    
    if (!validTypes.includes(selectedFile.type) && 
        !selectedFile.name.endsWith('.xlsx') && 
        !selectedFile.name.endsWith('.xls') && 
        !selectedFile.name.endsWith('.csv')) {
      toast.error('Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv');
      return;
    }
    
    setFile(selectedFile);
    setResults(null);
    toast.success(`Fichier "${selectedFile.name}" sélectionné`);
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Veuillez sélectionner un fichier');
      return;
    }

    try {
      setUploading(true);
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/orders/bulk-import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setResults(response.data);
      
      if (response.data.created > 0) {
        toast.success(`${response.data.created} commande(s) importée(s) avec succès !`);
      }
      
      if (response.data.failed > 0) {
        toast.warning(`${response.data.failed} ligne(s) avec erreurs`);
      }
      
    } catch (error) {
      console.error('Error uploading file:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors de l\'importation';
      toast.error(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'Hacen Tunisia, serif' }}>
            Importation de Commandes en Masse
          </h1>
          <p className="text-gray-600 mt-1">
            Importez vos commandes via un fichier Excel ou CSV avec calcul automatique des frais
          </p>
        </div>
        <Button onClick={handleDownloadTemplate} variant="outline" className="gap-2">
          <Download className="w-4 h-4" />
          Télécharger le Modèle
        </Button>
      </div>

      {/* Instructions Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3 flex items-center gap-2">
          <FileSpreadsheet className="w-5 h-5" />
          Comment utiliser l'importation ?
        </h3>
        <ol className="list-decimal list-inside space-y-2 text-blue-800">
          <li>Téléchargez le modèle Excel en cliquant sur le bouton ci-dessus</li>
          <li>Remplissez les colonnes : Nom Client, Téléphone, Wilaya, Commune, Adresse, Produit, Prix COD</li>
          <li>Assurez-vous que les noms de Wilayas sont correctement orthographiés</li>
          <li>Uploadez votre fichier rempli ci-dessous</li>
          <li>Le système calculera automatiquement les frais de livraison et le net à payer</li>
        </ol>
      </div>

      {/* Upload Zone */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive ? 'border-red-500 bg-red-50' : 'border-gray-300 bg-gray-50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          
          {!file ? (
            <>
              <p className="text-lg font-medium text-gray-700 mb-2">
                Glissez-déposez votre fichier ici
              </p>
              <p className="text-sm text-gray-500 mb-4">
                ou cliquez pour sélectionner (Excel .xlsx, .xls ou CSV)
              </p>
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileInput}
              />
              <label htmlFor="file-upload">
                <Button variant="outline" className="gap-2" asChild>
                  <span>
                    <FileSpreadsheet className="w-4 h-4" />
                    Sélectionner un fichier
                  </span>
                </Button>
              </label>
            </>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-3">
                <FileSpreadsheet className="w-8 h-8 text-green-600" />
                <div className="text-left">
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              
              <div className="flex items-center justify-center gap-3">
                <Button onClick={handleUpload} disabled={uploading} className="gap-2">
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Importation en cours...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Lancer l'importation
                    </>
                  )}
                </Button>
                
                <Button
                  onClick={() => setFile(null)}
                  variant="outline"
                  disabled={uploading}
                >
                  Annuler
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-4">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Lignes</p>
                  <p className="text-2xl font-bold text-gray-900">{results.total}</p>
                </div>
                <Package className="w-8 h-8 text-blue-500" />
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Importées</p>
                  <p className="text-2xl font-bold text-green-600">{results.created}</p>
                </div>
                <CheckCircle2 className="w-8 h-8 text-green-500" />
              </div>
            </div>

            <div className="bg-white p-4 rounded-lg border shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Erreurs</p>
                  <p className="text-2xl font-bold text-red-600">{results.failed}</p>
                </div>
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
            </div>
          </div>

          {/* Success List */}
          {results.success.length > 0 && (
            <div className="bg-white rounded-lg border shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                Commandes Créées ({results.success.length})
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="p-3 text-left text-sm font-semibold text-gray-700">Ligne</th>
                      <th className="p-3 text-left text-sm font-semibold text-gray-700">Tracking ID</th>
                      <th className="p-3 text-left text-sm font-semibold text-gray-700">Client</th>
                      <th className="p-3 text-right text-sm font-semibold text-gray-700">COD</th>
                      <th className="p-3 text-right text-sm font-semibold text-gray-700">Livraison</th>
                      <th className="p-3 text-right text-sm font-semibold text-gray-700 bg-green-50">NET</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {results.success.slice(0, 10).map((item, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="p-3 text-sm text-gray-600">{item.row}</td>
                        <td className="p-3">
                          <span className="font-mono text-sm text-blue-600">{item.tracking_id}</span>
                        </td>
                        <td className="p-3 text-sm text-gray-900">{item.client}</td>
                        <td className="p-3 text-right text-sm font-semibold">{item.cod.toFixed(2)} DZD</td>
                        <td className="p-3 text-right text-sm text-gray-600">{item.shipping.toFixed(2)} DZD</td>
                        <td className="p-3 text-right text-sm font-bold text-green-700 bg-green-50">
                          {item.net.toFixed(2)} DZD
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {results.success.length > 10 && (
                  <p className="text-sm text-gray-500 mt-3 text-center">
                    ... et {results.success.length - 10} autres commandes
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Errors List */}
          {results.errors.length > 0 && (
            <div className="bg-white rounded-lg border shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                Erreurs ({results.errors.length})
              </h3>
              <div className="space-y-2">
                {results.errors.map((error, index) => (
                  <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm font-medium text-red-900">
                      Ligne {error.row}: {error.error}
                    </p>
                    {error.data && (
                      <p className="text-xs text-red-700 mt-1">
                        {JSON.stringify(error.data).substring(0, 100)}...
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BulkImportPage;
