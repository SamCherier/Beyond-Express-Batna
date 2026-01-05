import React from 'react';
import { RefreshCw, CheckCircle2, Circle, Clock, Truck, Package, MapPin } from 'lucide-react';

/**
 * TrackingTimeline - Visual Timeline Component
 * 
 * Displays shipment progress with animated icons and color coding:
 * - Grey: Pending/Upcoming
 * - Blue: In Transit (with pulse animation)
 * - Green: Completed/Delivered
 * - Red: Returned/Failed
 */

const TrackingTimeline = ({ 
  timeline = [], 
  currentStatus, 
  terminalStatus,
  carrierType,
  carrierTrackingId,
  lastSyncAt,
  onSync,
  syncing = false 
}) => {
  // Status color mapping
  const getStatusColors = (status, isCompleted, isCurrent) => {
    if (isCompleted) {
      return {
        bg: 'bg-green-500',
        border: 'border-green-500',
        text: 'text-green-600',
        line: 'bg-green-500'
      };
    }
    if (isCurrent) {
      // Current step - Blue with pulse
      if (status === 'delivered') {
        return {
          bg: 'bg-green-500',
          border: 'border-green-500',
          text: 'text-green-600',
          line: 'bg-green-500'
        };
      }
      return {
        bg: 'bg-blue-500',
        border: 'border-blue-500',
        text: 'text-blue-600',
        line: 'bg-blue-500',
        pulse: true
      };
    }
    // Upcoming - Grey
    return {
      bg: 'bg-gray-200',
      border: 'border-gray-300',
      text: 'text-gray-400',
      line: 'bg-gray-200'
    };
  };

  // Icon mapping
  const getStepIcon = (status, isCompleted, isCurrent) => {
    const baseClass = "w-5 h-5";
    
    if (isCompleted) {
      return <CheckCircle2 className={`${baseClass} text-white`} />;
    }
    
    switch (status) {
      case 'pending':
        return <Clock className={`${baseClass} ${isCurrent ? 'text-white' : 'text-gray-400'}`} />;
      case 'preparing':
      case 'ready_to_ship':
        return <Package className={`${baseClass} ${isCurrent ? 'text-white' : 'text-gray-400'}`} />;
      case 'picked_up':
      case 'in_transit':
      case 'out_for_delivery':
        return <Truck className={`${baseClass} ${isCurrent ? 'text-white' : 'text-gray-400'}`} />;
      case 'delivered':
        return <CheckCircle2 className={`${baseClass} ${isCurrent ? 'text-white' : 'text-gray-400'}`} />;
      default:
        return <Circle className={`${baseClass} ${isCurrent ? 'text-white' : 'text-gray-400'}`} />;
    }
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return null;
    const date = new Date(timestamp);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6">
      {/* Header with Sync Button */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <MapPin className="w-5 h-5 text-blue-500" />
            Suivi en Direct
          </h3>
          {carrierType && (
            <p className="text-sm text-gray-500 mt-1">
              {carrierType === 'zr_express' ? 'ZR Express' : carrierType === 'yalidine' ? 'Yalidine' : carrierType}
              {carrierTrackingId && <span className="ml-2 font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">{carrierTrackingId}</span>}
            </p>
          )}
        </div>
        
        <button
          onClick={onSync}
          disabled={syncing}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
            syncing 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-blue-500 hover:bg-blue-600 text-white shadow-md hover:shadow-lg'
          }`}
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Sync...' : 'Actualiser'}
        </button>
      </div>

      {/* Last Sync Info */}
      {lastSyncAt && (
        <p className="text-xs text-gray-400 mb-4">
          Dernière sync: {formatTime(lastSyncAt)}
        </p>
      )}

      {/* Timeline - Horizontal for desktop, vertical for mobile */}
      <div className="relative">
        {/* Horizontal Timeline (Desktop) */}
        <div className="hidden md:flex items-start justify-between relative">
          {/* Progress Line */}
          <div className="absolute top-5 left-0 right-0 h-1 bg-gray-200 rounded-full">
            <div 
              className="h-full bg-gradient-to-r from-green-500 to-blue-500 rounded-full transition-all duration-500"
              style={{ 
                width: `${Math.max(0, (timeline.findIndex(t => t.current) / (timeline.length - 1)) * 100)}%` 
              }}
            />
          </div>
          
          {timeline.map((step, index) => {
            const colors = getStatusColors(step.status, step.completed, step.current);
            return (
              <div key={step.status} className="flex flex-col items-center z-10 flex-1">
                {/* Circle with Icon */}
                <div 
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${colors.bg} ${colors.border} border-2 shadow-md transition-all duration-300 ${
                    colors.pulse ? 'animate-pulse ring-4 ring-blue-200' : ''
                  }`}
                >
                  {getStepIcon(step.status, step.completed, step.current)}
                </div>
                
                {/* Label */}
                <span className={`mt-2 text-xs font-medium ${colors.text} text-center max-w-[80px]`}>
                  {step.label}
                </span>
                
                {/* Timestamp */}
                {step.timestamp && (
                  <span className="mt-1 text-[10px] text-gray-400">
                    {formatTime(step.timestamp)}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Vertical Timeline (Mobile) */}
        <div className="md:hidden space-y-0">
          {timeline.map((step, index) => {
            const colors = getStatusColors(step.status, step.completed, step.current);
            const isLast = index === timeline.length - 1;
            
            return (
              <div key={step.status} className="flex items-start gap-4">
                {/* Circle and Line */}
                <div className="flex flex-col items-center">
                  <div 
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${colors.bg} ${colors.border} border-2 shadow-md transition-all duration-300 ${
                      colors.pulse ? 'animate-pulse ring-4 ring-blue-200' : ''
                    }`}
                  >
                    {getStepIcon(step.status, step.completed, step.current)}
                  </div>
                  {!isLast && (
                    <div className={`w-0.5 h-12 ${step.completed ? 'bg-green-500' : 'bg-gray-200'}`} />
                  )}
                </div>
                
                {/* Content */}
                <div className="flex-1 pb-8">
                  <p className={`font-medium ${colors.text}`}>
                    {step.icon} {step.label}
                  </p>
                  {step.timestamp && (
                    <p className="text-xs text-gray-400 mt-0.5">
                      {formatTime(step.timestamp)}
                    </p>
                  )}
                  {step.location && (
                    <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {step.location}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Terminal Status (Returned/Failed/Cancelled) */}
      {terminalStatus && (
        <div 
          className="mt-6 p-4 rounded-lg border-2"
          style={{ 
            backgroundColor: `${terminalStatus.color}10`,
            borderColor: terminalStatus.color 
          }}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">{terminalStatus.icon}</span>
            <div>
              <p className="font-bold" style={{ color: terminalStatus.color }}>
                {terminalStatus.label}
              </p>
              <p className="text-sm text-gray-500">
                Statut terminal - Aucune mise à jour attendue
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ZR Express Mock Notice */}
      {carrierType === 'zr_express' && (
        <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg">
          <p className="text-xs text-amber-700 dark:text-amber-400 flex items-center gap-2">
            <span>⚡</span>
            <span>
              <strong>Mode Démo:</strong> Cliquez sur "Actualiser" pour simuler l'avancement du colis (Time Travel)
            </span>
          </p>
        </div>
      )}
    </div>
  );
};

export default TrackingTimeline;
