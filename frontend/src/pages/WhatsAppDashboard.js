import React, { useState, useEffect } from 'react';
import { Bell, MessageCircle, Send, Settings, TrendingUp, CheckCircle, XCircle, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import api from '@/api';
import PhonePreview from '@/components/PhonePreview';
import { useAuth } from '@/contexts/AuthContext';

const WhatsAppDashboard = () => {
  const { user } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [previewMessage, setPreviewMessage] = useState('');
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Admin has access to everything, PRO and BUSINESS plans have access
  const hasAccess = user?.role === 'admin' || ['pro', 'business', 'PRO', 'BUSINESS'].includes(user?.subscription_plan);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [templatesRes, statsRes, historyRes] = await Promise.all([
        api.get('/notifications/templates'),
        api.get('/notifications/stats'),
        api.get('/notifications/history?limit=10')
      ]);

      setTemplates(templatesRes.data.templates);
      setStats(statsRes.data);
      setHistory(historyRes.data.notifications);

      // Set first template as selected
      if (templatesRes.data.templates.length > 0) {
        const firstTemplate = templatesRes.data.templates[0];
        setSelectedTemplate(firstTemplate);
        setPreviewMessage(replaceVariables(firstTemplate.message));
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const replaceVariables = (message) => {
    // Replace template variables with example values
    return message
      .replace(/{name}/g, 'Ahmed')
      .replace(/{product}/g, 'Samsung A54')
      .replace(/{price}/g, '45,000')
      .replace(/{tracking_id}/g, 'TRK123456')
      .replace(/{total_cod}/g, '45,000');
  };

  const handleTemplateChange = (template) => {
    setSelectedTemplate(template);
    setPreviewMessage(replaceVariables(template.message));
  };

  const handleMessageChange = (e) => {
    const newMessage = e.target.value;
    setSelectedTemplate({ ...selectedTemplate, message: newMessage });
    setPreviewMessage(replaceVariables(newMessage));
  };

  const handleToggleTemplate = (index) => {
    const newTemplates = [...templates];
    newTemplates[index].enabled = !newTemplates[index].enabled;
    setTemplates(newTemplates);
  };

  const handleSaveTemplates = async () => {
    try {
      await api.put('/notifications/templates', { templates });
      toast.success('Templates sauvegardés avec succès !');
    } catch (error) {
      console.error('Error saving templates:', error);
      toast.error('Erreur lors de la sauvegarde');
    }
  };

  const templateIcons = {
    order_confirmed: <CheckCircle className="w-5 h-5" />,
    out_for_delivery: <Send className="w-5 h-5" />,
    delivery_failed: <XCircle className="w-5 h-5" />,
    delivered: <CheckCircle className="w-5 h-5" />
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  if (!hasAccess) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20 border-red-200 dark:border-red-900">
          <CardContent className="pt-6">
            <div className="text-center">
              <MessageCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
              <h3 className="text-2xl font-bold mb-2 text-gray-900 dark:text-white">Fonctionnalité Premium</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Les notifications WhatsApp automatisées sont disponibles avec le plan <span className="font-bold text-red-600">PRO</span>.
              </p>
              <Button className="bg-red-500 hover:bg-red-600 text-white">
                Passer au Plan PRO
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <MessageCircle className="w-8 h-8 text-green-500" />
            Notifications WhatsApp
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Automatisez vos communications client par WhatsApp
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Envoyés</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">{stats.total || 0}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Messages simulés (MVP)</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Taux de Réussite</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">100%</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Mode simulation</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Plus Utilisé</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-gray-900 dark:text-white">
                {stats.by_type && Object.keys(stats.by_type).length > 0 
                  ? Object.entries(stats.by_type).sort((a, b) => b[1] - a[1])[0][0]
                  : 'N/A'
                }
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Template le plus utilisé</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Templates Editor */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Templates de Messages
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Template Tabs */}
              <div className="flex gap-2 overflow-x-auto pb-2">
                {templates.map((template, index) => (
                  <button
                    key={index}
                    onClick={() => handleTemplateChange(template)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all flex items-center gap-2 ${
                      selectedTemplate?.type === template.type
                        ? 'bg-green-500 text-white shadow-md'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                    }`}
                  >
                    {templateIcons[template.type]}
                    {template.name}
                  </button>
                ))}
              </div>

              {/* Template Editor */}
              {selectedTemplate && (
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <Label>Message</Label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedTemplate.enabled}
                          onChange={() => {
                            const index = templates.findIndex(t => t.type === selectedTemplate.type);
                            handleToggleTemplate(index);
                          }}
                          className="rounded"
                        />
                        <span className="text-sm text-gray-600 dark:text-gray-400">Activé</span>
                      </label>
                    </div>
                    <textarea
                      value={selectedTemplate.message}
                      onChange={handleMessageChange}
                      rows={5}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      placeholder="Écrivez votre message..."
                    />
                  </div>

                  <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg p-4">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-400 mb-2">Variables Disponibles:</p>
                    <div className="flex flex-wrap gap-2">
                      {['{name}', '{product}', '{price}', '{tracking_id}', '{total_cod}'].map((variable) => (
                        <code key={variable} className="px-2 py-1 bg-white dark:bg-gray-800 border border-blue-300 dark:border-blue-800 rounded text-xs text-blue-600 dark:text-blue-400">
                          {variable}
                        </code>
                      ))}
                    </div>
                  </div>

                  <Button onClick={handleSaveTemplates} className="bg-green-500 hover:bg-green-600 text-white w-full">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Sauvegarder les Templates
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Historique Récent
              </CardTitle>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-center py-8">Aucune notification envoyée pour le moment</p>
              ) : (
                <div className="space-y-3">
                  {history.map((notif, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-950 flex items-center justify-center">
                          <MessageCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{notif.recipient_name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{notif.template_type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(notif.created_at).toLocaleDateString('fr-FR')}
                        </p>
                        <span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-950 text-green-600 dark:text-green-400 rounded-full">
                          Simulé
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Phone Preview */}
        <div className="lg:col-span-1">
          <PhonePreview message={previewMessage} recipientName="Ahmed" />
        </div>
      </div>
    </div>
  );
};

export default WhatsAppDashboard;
