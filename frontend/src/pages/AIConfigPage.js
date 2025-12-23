import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Brain, Key, CheckCircle, XCircle, ExternalLink, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/api';

const AIConfigPage = () => {
  const [provider, setProvider] = useState('gemini');
  const [apiKey, setApiKey] = useState('');
  const [maskedKey, setMaskedKey] = useState('****');
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await api.get('/ai-config/config');
      setProvider(response.data.provider || 'gemini');
      setMaskedKey(response.data.api_key_masked || '****');
    } catch (error) {
      console.error('Error fetching config:', error);
    }
  };

  const handleSaveConfig = async () => {
    if (!apiKey) {
      toast.error('Veuillez entrer une clé API');
      return;
    }

    try {
      setLoading(true);
      await api.post('/ai-config/config', {
        provider,
        api_key: apiKey,
        model_name: 'gemini-pro'  // Use stable model instead of flash
      });

      toast.success('Configuration sauvegardée avec succès !');
      setApiKey('');
      fetchConfig();
    } catch (error) {
      console.error('Error saving config:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    } finally {
      setLoading(false);
    }
  };

  const handleTestAI = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      
      const response = await api.post('/ai-config/test', {
        message: 'Bonjour, peux-tu te présenter ?'
      });

      setTestResult(response.data);
      
      if (response.data.success) {
        toast.success('Test réussi ! L\'IA fonctionne correctement.');
      } else {
        toast.error('Test échoué. Vérifiez votre clé API.');
      }
    } catch (error) {
      console.error('Error testing AI:', error);
      setTestResult({
        success: false,
        error: error.response?.data?.detail || 'Erreur de connexion'
      });
      toast.error('Test échoué. Vérifiez votre configuration.');
    } finally {
      setTesting(false);
    }
  };

  const providers = [
    {
      value: 'gemini',
      label: 'Google Gemini (Gratuit)',
      description: 'Modèle rapide et puissant de Google',
      helpLink: 'https://aistudio.google.com/apikey',
      helpText: 'Récupérer une clé Gemini gratuite'
    },
    {
      value: 'deepseek',
      label: 'DeepSeek V3',
      description: 'Modèle open-source performant',
      helpLink: 'https://platform.deepseek.com',
      helpText: 'Créer un compte DeepSeek'
    },
    {
      value: 'openai',
      label: 'OpenAI',
      description: 'GPT-4 et autres modèles OpenAI',
      helpLink: 'https://platform.openai.com/api-keys',
      helpText: 'Obtenir une clé OpenAI'
    }
  ];

  const selectedProvider = providers.find(p => p.value === provider);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <Brain className="w-8 h-8 text-purple-500" />
          Configuration de l'IA
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Configurez votre assistant IA avec votre propre clé API (BYOK)
        </p>
      </div>

      {/* Main Config Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="w-5 h-5" />
            Configuration du Fournisseur
          </CardTitle>
          <CardDescription>
            Choisissez votre fournisseur d'IA et entrez votre clé API
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Provider Selection */}
          <div>
            <Label htmlFor="provider" className="mb-2 block">Fournisseur d'IA</Label>
            <Select value={provider} onValueChange={setProvider}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {providers.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    <div className="flex flex-col">
                      <span className="font-medium">{p.label}</span>
                      <span className="text-xs text-gray-500">{p.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Help Link */}
          {selectedProvider && (
            <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg p-4">
              <p className="text-sm text-blue-900 dark:text-blue-400 mb-2">
                Besoin d'une clé API ?
              </p>
              <a
                href={selectedProvider.helpLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                <ExternalLink className="w-4 h-4" />
                {selectedProvider.helpText}
              </a>
            </div>
          )}

          {/* API Key Input */}
          <div>
            <Label htmlFor="apiKey" className="mb-2 block">Clé API</Label>
            <div className="space-y-2">
              <Input
                id="apiKey"
                type="password"
                placeholder="Entrez votre clé API..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="font-mono"
              />
              {maskedKey !== '****' && (
                <p className="text-xs text-gray-500">
                  Clé actuelle : <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">{maskedKey}</code>
                </p>
              )}
            </div>
          </div>

          {/* Save Button */}
          <Button
            onClick={handleSaveConfig}
            disabled={loading || !apiKey}
            className="w-full bg-purple-500 hover:bg-purple-600 text-white"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Sauvegarde...
              </>
            ) : (
              <>
                <Key className="w-4 h-4 mr-2" />
                Sauvegarder la Configuration
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Test Card */}
      <Card>
        <CardHeader>
          <CardTitle>Tester la Connexion</CardTitle>
          <CardDescription>
            Vérifiez que votre configuration fonctionne correctement
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            onClick={handleTestAI}
            disabled={testing || maskedKey === '****'}
            variant="outline"
            className="w-full"
          >
            {testing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Test en cours...
              </>
            ) : (
              <>
                <Brain className="w-4 h-4 mr-2" />
                Tester l'IA
              </>
            )}
          </Button>

          {testResult && (
            <div className={`p-4 rounded-lg border ${
              testResult.success 
                ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900' 
                : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900'
            }`}>
              <div className="flex items-start gap-3">
                {testResult.success ? (
                  <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className={`font-medium mb-1 ${
                    testResult.success 
                      ? 'text-green-900 dark:text-green-400' 
                      : 'text-red-900 dark:text-red-400'
                  }`}>
                    {testResult.success ? 'Test réussi !' : 'Test échoué'}
                  </p>
                  {testResult.response && (
                    <p className="text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 p-3 rounded mt-2">
                      {testResult.response}
                    </p>
                  )}
                  {testResult.error && (
                    <p className="text-sm text-red-700 dark:text-red-400">
                      {testResult.error}
                    </p>
                  )}
                  {testResult.provider && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Fournisseur : {testResult.provider} | Modèle : {testResult.model}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20 border-purple-200 dark:border-purple-900">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-purple-900 dark:text-purple-400 mb-2">
            Pourquoi BYOK (Bring Your Own Key) ?
          </h3>
          <ul className="space-y-2 text-sm text-purple-800 dark:text-purple-300">
            <li className="flex items-start gap-2">
              <span className="text-purple-500">•</span>
              <span><strong>Gratuit</strong> : Utilisez les quotas gratuits de Gemini (60 req/min)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-500">•</span>
              <span><strong>Contrôle</strong> : Vos données restent entre vous et le fournisseur</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-500">•</span>
              <span><strong>Flexible</strong> : Changez de fournisseur à tout moment</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIConfigPage;
