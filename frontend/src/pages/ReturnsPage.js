import React, { useState } from 'react';
import { Search, Package, AlertTriangle, CheckCircle, XCircle, TrendingUp, BarChart3, Trash2, Archive, ClipboardCheck } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

/**
 * SMART RETURNS - RMA Management (MOCKUP VISUAL ONLY)
 * 
 * Workflow intelligent de gestion des retours
 * Données statiques pour démo investisseurs
 */

// Mock data
const MOCK_RETURNS = [
  {
    id: 'RET-001',
    trackingId: 'BEX-A1B2C3D4',
    customer: 'Mohamed Amrani',
    wilaya: 'Alger',
    reason: 'Client Absent',
    status: 'restock',
    decision: '📦 Remise en Stock (Zone A2)',
    badgeColor: 'bg-green-600',
    timestamp: '2025-01-11 14:30'
  },
  {
    id: 'RET-002',
    trackingId: 'BEX-E5F6G7H8',
    customer: 'Sarah Benali',
    wilaya: 'Oran',
    reason: 'Produit Endommagé',
    status: 'discard',
    decision: '🗑️ Mise au Rebut',
    badgeColor: 'bg-red-600',
    timestamp: '2025-01-11 13:15'
  },
  {
    id: 'RET-003',
    trackingId: 'BEX-I9J0K1L2',
    customer: 'Karim Boudiaf',
    wilaya: 'Constantine',
    reason: 'Refus (Prix)',
    status: 'inspect',
    decision: '⚠️ Contrôle Qualité',
    badgeColor: 'bg-yellow-600',
    timestamp: '2025-01-11 11:45'
  },
  {
    id: 'RET-004',
    trackingId: 'BEX-M3N4O5P6',
    customer: 'Amina Cherif',
    wilaya: 'Sétif',
    reason: 'Erreur Adresse',
    status: 'restock',
    decision: '📦 Remise en Stock (Zone B1)',
    badgeColor: 'bg-green-600',
    timestamp: '2025-01-11 10:20'
  },
  {
    id: 'RET-005',
    trackingId: 'BEX-Q7R8S9T0',
    customer: 'Yacine Djamel',
    wilaya: 'Batna',
    reason: 'Client Absent',
    status: 'restock',
    decision: '📦 Remise en Stock (Zone A2)',
    badgeColor: 'bg-green-600',
    timestamp: '2025-01-11 09:30'
  }
];

const RETURN_REASONS_STATS = [
  { reason: 'Client Absent', percentage: 40, color: 'bg-blue-500' },
  { reason: 'Refus (Prix)', percentage: 25, color: 'bg-orange-500' },
  { reason: 'Produit Endommagé', percentage: 20, color: 'bg-red-500' },
  { reason: 'Erreur Adresse', percentage: 15, color: 'bg-purple-500' }
];

const ReturnsPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedReturn, setSelectedReturn] = useState(null);
  
  const filteredReturns = MOCK_RETURNS.filter(ret => 
    ret.trackingId.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ret.customer.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
          <Package className="w-10 h-10 text-cyan-400" />
          Smart Returns - RMA
        </h1>
        <p className="text-gray-400">Gestion intelligente des retours avec décisions IA</p>
      </div>
      
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card className="glass-card border-cyan-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Retours</p>
                <p className="text-3xl font-bold text-white mt-1">127</p>
                <p className="text-xs text-cyan-400 mt-1">+8% cette semaine</p>
              </div>
              <TrendingUp className="w-10 h-10 text-cyan-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass-card border-green-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Remis en Stock</p>
                <p className="text-3xl font-bold text-white mt-1">85</p>
                <p className="text-xs text-green-400 mt-1">67% du total</p>
              </div>
              <Archive className="w-10 h-10 text-green-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass-card border-red-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Mis au Rebut</p>
                <p className="text-3xl font-bold text-white mt-1">18</p>
                <p className="text-xs text-red-400 mt-1">14% du total</p>
              </div>
              <Trash2 className="w-10 h-10 text-red-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="glass-card border-yellow-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">En Contrôle</p>
                <p className="text-3xl font-bold text-white mt-1">24</p>
                <p className="text-xs text-yellow-400 mt-1">19% du total</p>
              </div>
              <ClipboardCheck className="w-10 h-10 text-yellow-400" />
            </div>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Returns List */}
        <div className="lg:col-span-2">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center justify-between">
                <span>Retours Récents</span>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Rechercher tracking ID..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-white/10 border-white/20 text-white"
                  />
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {filteredReturns.map(ret => (
                  <div
                    key={ret.id}
                    className="p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all cursor-pointer"
                    onClick={() => setSelectedReturn(ret)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-mono text-white font-bold">{ret.trackingId}</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-bold text-white ${ret.badgeColor}`}>
                            {ret.decision}
                          </span>
                        </div>
                        <p className="text-gray-300 text-sm">{ret.customer} • {ret.wilaya}</p>
                        <p className="text-gray-400 text-xs mt-1">Motif: {ret.reason}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-400">{ret.timestamp}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Stats Chart */}
        <div className="lg:col-span-1">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Motifs de Retour
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {RETURN_REASONS_STATS.map((stat, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-300">{stat.reason}</span>
                      <span className="text-sm font-bold text-white">{stat.percentage}%</span>
                    </div>
                    <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${stat.color} transition-all duration-500`}
                        style={{ width: `${stat.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 p-4 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                <p className="text-xs text-cyan-300 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span>L'IA recommande de contacter les clients "Absent" par SMS automatique</span>
                </p>
              </div>
            </CardContent>
          </Card>
          
          {/* Coming Soon Badge */}
          <Card className="glass-card mt-6 border-purple-500/50">
            <CardContent className="p-6 text-center">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-500/20 mb-3">
                  <Package className="w-8 h-8 text-purple-400" />
                </div>
              </div>
              <h3 className="text-white font-bold mb-2">Fonctionnalité en Développement</h3>
              <p className="text-gray-400 text-sm">
                Module complet de workflow RMA avec scan barcode, photos de preuve, et décisions IA automatiques.
              </p>
              <p className="text-purple-400 text-xs mt-3 font-semibold">Disponible en Phase B</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ReturnsPage;
