import React, { useState, useEffect } from 'react';
import { Phone, MapPin, CheckCircle, XCircle, Package, Navigation } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import api from '@/api';

const DriverTasks = () => {
  const { user } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, totalAmount: 0 });
  const [selectedTask, setSelectedTask] = useState(null);
  const [showFailModal, setShowFailModal] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await api.get('/driver/tasks');
      const tasksList = response.data.tasks || [];
      
      // Map backend structure (client) to frontend structure (recipient)
      const mappedTasks = tasksList.map(task => ({
        ...task,
        id: task.order_id,
        recipient: {
          name: task.client?.name || 'N/A',
          phone: task.client?.phone || 'N/A',
          address: task.client?.address || 'N/A',
          wilaya: task.client?.wilaya || 'N/A',
          commune: task.client?.commune || 'N/A'
        }
      }));
      
      setTasks(mappedTasks);
      
      // Calculate stats
      const total = mappedTasks.length;
      const totalAmount = mappedTasks.reduce((sum, task) => sum + (task.cod_amount || 0), 0);
      setStats({ total, totalAmount });
    } catch (error) {
      console.error('Error fetching tasks:', error);
      toast.error('Erreur lors du chargement des tâches');
    } finally {
      setLoading(false);
    }
  };

  const handleCall = (phone) => {
    window.location.href = `tel:${phone}`;
  };

  const handleNavigate = (address, wilaya, commune) => {
    const fullAddress = `${address}, ${commune}, ${wilaya}, Algeria`;
    const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(fullAddress)}`;
    window.open(mapsUrl, '_blank');
  };

  const handleDeliver = async (taskId) => {
    try {
      await api.post('/driver/update-status', {
        order_id: taskId,
        status: 'delivered',
        notes: 'Livré avec succès'
      });
      
      toast.success('✅ Colis marqué comme livré !');
      fetchTasks(); // Refresh
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleFail = async (taskId, reason) => {
    try {
      await api.post('/driver/update-status', {
        order_id: taskId,
        status: 'delivery_failed',
        notes: reason
      });
      
      toast.error('❌ Échec de livraison enregistré');
      setShowFailModal(false);
      setSelectedTask(null);
      fetchTasks(); // Refresh
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const failReasons = [
    'Client absent',
    'Refus du colis',
    'Adresse incorrecte',
    'Téléphone éteint',
    'Reprogrammer livraison'
  ];

  const getStatusColor = (status) => {
    const colors = {
      'ready_to_ship': 'bg-blue-100 text-blue-800',
      'in_transit': 'bg-orange-100 text-orange-800',
      'delivered': 'bg-green-100 text-green-800',
      'delivery_failed': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 max-w-2xl mx-auto">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-red-600 to-orange-600 rounded-2xl p-6 text-white mb-6 shadow-lg">
        <h2 className="text-2xl font-bold mb-2">Bonjour {user?.name?.split(' ')[0] || 'Chauffeur'} 👋</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-3xl font-bold">{stats.total}</p>
            <p className="text-red-100">Colis aujourd'hui</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold">{stats.totalAmount.toLocaleString()} DA</p>
            <p className="text-red-100">Total à encaisser</p>
          </div>
        </div>
      </div>

      {/* Tasks List */}
      {tasks.length === 0 ? (
        <div className="text-center py-12">
          <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-xl text-gray-600 font-semibold">Aucun colis assigné</p>
          <p className="text-gray-500">Vérifiez plus tard</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <div key={task.id} className="bg-white rounded-xl shadow-md overflow-hidden border-2 border-gray-200">
              {/* Header */}
              <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between">
                <div>
                  <p className="font-bold text-gray-900">{task.recipient?.name || 'Client'}</p>
                  <p className="text-sm text-gray-600">{task.tracking_id}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(task.status)}`}>
                  {task.status}
                </span>
              </div>

              {/* Location */}
              <div className="px-4 py-4 border-b">
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-red-600 flex-shrink-0 mt-1" />
                  <div>
                    <p className="font-medium text-gray-900">{task.recipient?.wilaya}</p>
                    <p className="text-sm text-gray-600">{task.recipient?.commune}</p>
                    <p className="text-xs text-gray-500 mt-1">{task.recipient?.address}</p>
                  </div>
                </div>
              </div>

              {/* Amount */}
              <div className="bg-green-50 px-4 py-4 border-b">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700 font-medium">Montant à encaisser :</span>
                  <span className="text-3xl font-bold text-green-600">{task.cod_amount?.toLocaleString() || 0} DA</span>
                </div>
              </div>

              {/* Actions */}
              <div className="p-4 space-y-3">
                {/* Contact Actions */}
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    onClick={() => handleCall(task.recipient?.phone)}
                    className="h-14 bg-blue-600 hover:bg-blue-700 text-white font-bold"
                  >
                    <Phone className="w-5 h-5 mr-2" />
                    Appeler
                  </Button>
                  <Button
                    onClick={() => handleNavigate(task.recipient?.address, task.recipient?.wilaya, task.recipient?.commune)}
                    className="h-14 bg-purple-600 hover:bg-purple-700 text-white font-bold"
                  >
                    <Navigation className="w-5 h-5 mr-2" />
                    GPS
                  </Button>
                </div>

                {/* Status Actions */}
                {task.status !== 'delivered' && task.status !== 'delivery_failed' && (
                  <div className="grid grid-cols-2 gap-3">
                    <Button
                      onClick={() => handleDeliver(task.id)}
                      className="h-14 bg-green-600 hover:bg-green-700 text-white font-bold"
                    >
                      <CheckCircle className="w-5 h-5 mr-2" />
                      LIVRÉ
                    </Button>
                    <Button
                      onClick={() => {
                        setSelectedTask(task);
                        setShowFailModal(true);
                      }}
                      className="h-14 bg-red-600 hover:bg-red-700 text-white font-bold"
                    >
                      <XCircle className="w-5 h-5 mr-2" />
                      ÉCHEC
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Fail Reason Modal */}
      {showFailModal && selectedTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold mb-4 text-gray-900">Raison de l'échec</h3>
            <p className="text-sm text-gray-600 mb-4">Pourquoi n'avez-vous pas pu livrer ce colis ?</p>
            
            <div className="space-y-2 mb-6">
              {failReasons.map((reason) => (
                <button
                  key={reason}
                  onClick={() => handleFail(selectedTask.id, reason)}
                  className="w-full p-4 text-left border-2 border-gray-200 rounded-lg hover:border-red-500 hover:bg-red-50 transition-colors"
                >
                  {reason}
                </button>
              ))}
            </div>

            <Button
              onClick={() => {
                setShowFailModal(false);
                setSelectedTask(null);
              }}
              variant="outline"
              className="w-full"
            >
              Annuler
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DriverTasks;
