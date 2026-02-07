import React from 'react';
import { Warehouse, TrendingUp, AlertTriangle, Package, Thermometer, Shield, Box } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

/**
 * VISUAL WAREHOUSE - Stock Management (MOCKUP VISUAL ONLY)
 * 
 * Visualisation isométrique des zones de stockage
 * Données statiques pour démo investisseurs
 */

const WAREHOUSE_ZONES = [
  {
    id: 'A1',
    name: 'Zone Froide A1',
    type: 'cold',
    icon: Thermometer,
    capacity: 100,
    used: 68,
    color: 'cyan',
    status: 'optimal',
    temperature: '4°C'
  },
  {
    id: 'A2',
    name: 'Zone Sèche A2',
    type: 'dry',
    icon: Box,
    capacity: 200,
    used: 170,
    color: 'green',
    status: 'warning',
    temperature: '20°C'
  },
  {
    id: 'B1',
    name: 'Zone Fragile B1',
    type: 'fragile',
    icon: Shield,
    capacity: 150,
    used: 95,
    color: 'orange',
    status: 'optimal',
    temperature: '18°C'
  },
  {
    id: 'B2',
    name: 'Zone Standard B2',
    type: 'standard',
    icon: Package,
    capacity: 300,
    used: 255,
    color: 'purple',
    status: 'critical',
    temperature: '22°C'
  }
];

const DEPOT_STATS = [
  { city: 'Alger', capacity: 85, color: 'bg-orange-500', status: 'warning' },
  { city: 'Oran', capacity: 62, color: 'bg-green-500', status: 'optimal' },
  { city: 'Constantine', capacity: 91, color: 'bg-red-500', status: 'critical' },
  { city: 'Batna', capacity: 45, color: 'bg-green-500', status: 'optimal' }
];

const WarehousePage = () => {
  const totalCapacity = WAREHOUSE_ZONES.reduce((sum, zone) => sum + zone.capacity, 0);
  const totalUsed = WAREHOUSE_ZONES.reduce((sum, zone) => sum + zone.used, 0);
  const overallPercentage = Math.round((totalUsed / totalCapacity) * 100);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
          <Warehouse className="w-10 h-10 text-cyan-400" />
          Visual Warehouse
        </h1>
        <p className="text-gray-400">Gestion intelligente de capacité & zones de stockage</p>
      </div>
      
      {/* Overall Capacity */}
      <Card className="glass-card mb-8">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-white">Capacité Globale Entrepôt</h2>
              <p className="text-gray-400">Utilisation actuelle: {totalUsed} / {totalCapacity} emplacements</p>
            </div>
            <div className="text-right">
              <p className="text-5xl font-bold text-white">{overallPercentage}%</p>
              <p className={`text-sm font-semibold ${overallPercentage > 80 ? 'text-red-400' : 'text-green-400'}`}>
                {overallPercentage > 80 ? '⚠️ Alerte Capacité' : '✅ Optimal'}
              </p>
            </div>
          </div>
          
          {/* Segmented Progress Bar */}
          <div className="relative h-8 bg-white/10 rounded-full overflow-hidden">
            {WAREHOUSE_ZONES.map((zone, idx) => {
              const percentage = (zone.used / totalCapacity) * 100;
              const left = WAREHOUSE_ZONES.slice(0, idx).reduce((sum, z) => sum + (z.used / totalCapacity) * 100, 0);
              
              return (
                <div
                  key={zone.id}
                  className={`absolute top-0 h-full bg-${zone.color}-500 transition-all duration-500 hover:opacity-80 cursor-pointer`}
                  style={{
                    left: `${left}%`,
                    width: `${percentage}%`
                  }}
                  title={`${zone.name}: ${zone.used}/${zone.capacity}`}
                />
              );
            })}
          </div>
          
          {/* Legend */}
          <div className="flex flex-wrap gap-4 mt-4">
            {WAREHOUSE_ZONES.map(zone => (
              <div key={zone.id} className="flex items-center gap-2">
                <div className={`w-4 h-4 rounded bg-${zone.color}-500`} />
                <span className="text-sm text-gray-300">{zone.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      {/* Zones Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {WAREHOUSE_ZONES.map(zone => {
          const percentage = Math.round((zone.used / zone.capacity) * 100);
          const Icon = zone.icon;
          
          return (
            <Card key={zone.id} className={`glass-card border-${zone.color}-500/30 hover:scale-105 transition-transform`}>
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Icon className={`w-5 h-5 text-${zone.color}-400`} />
                  {zone.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {/* Isometric Icon Representation */}
                <div className="mb-4 flex justify-center">
                  <div className={`relative w-24 h-24 bg-gradient-to-br from-${zone.color}-500/20 to-${zone.color}-600/40 rounded-lg flex items-center justify-center transform rotate-45 overflow-hidden`}>
                    <div className="transform -rotate-45">
                      <Icon className={`w-12 h-12 text-${zone.color}-400`} />
                    </div>
                  </div>
                </div>
                
                {/* Stats */}
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-400">Occupation</span>
                      <span className="text-sm font-bold text-white">{percentage}%</span>
                    </div>
                    <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full bg-${zone.color}-500 transition-all duration-500`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Utilisé:</span>
                    <span className="text-white font-semibold">{zone.used} / {zone.capacity}</span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Temp:</span>
                    <span className="text-cyan-400 font-semibold">{zone.temperature}</span>
                  </div>
                  
                  <div className={`px-3 py-1 rounded-full text-xs font-bold text-center ${
                    zone.status === 'optimal' ? 'bg-green-500/20 text-green-400' :
                    zone.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-red-500/20 text-red-400'
                  }`}>
                    {zone.status === 'optimal' ? '✅ Optimal' :
                     zone.status === 'warning' ? '⚠️ Attention' :
                     '🚨 Critique'}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      
      {/* Regional Depots */}
      <Card className="glass-card mb-6">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            Dépôts Régionaux (Wilayas)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {DEPOT_STATS.map((depot, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-white/5 border border-white/10">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold text-white">{depot.city}</h3>
                  <span className={`text-2xl font-bold ${
                    depot.status === 'optimal' ? 'text-green-400' :
                    depot.status === 'warning' ? 'text-yellow-400' :
                    'text-red-400'
                  }`}>
                    {depot.capacity}%
                  </span>
                </div>
                <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${depot.color} transition-all duration-500`}
                    style={{ width: `${depot.capacity}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {depot.status === 'critical' ? 'Réapprovisionnement urgent' : 
                   depot.status === 'warning' ? 'Surveiller la capacité' : 
                   'Fonctionnement normal'}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      {/* Coming Soon */}
      <Card className="glass-card border-purple-500/50">
        <CardContent className="p-6 text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-500/20 mb-3">
              <Warehouse className="w-8 h-8 text-purple-400" />
            </div>
          </div>
          <h3 className="text-white font-bold mb-2">Module Complet en Développement</h3>
          <p className="text-gray-400 text-sm mb-4">
            Interface 3D isométrique interactive avec drag & drop pour réorganisation des zones,
            alertes automatiques de réapprovisionnement, et intégration IoT pour température en temps réel.
          </p>
          <div className="flex items-center justify-center gap-2 text-purple-400 text-xs font-semibold">
            <AlertTriangle className="w-4 h-4" />
            <span>Disponible en Phase B - Q1 2025</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WarehousePage;
