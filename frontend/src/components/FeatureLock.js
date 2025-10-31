import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Crown, Zap, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * Composant pour afficher un message de verrouillage et encourager l'upgrade
 * 
 * Utilisation:
 * <FeatureLock 
 *   feature="pro_dashboard" 
 *   message="Passez au plan PRO pour accéder aux statistiques avancées"
 *   requiredPlan="pro"
 * />
 */
const FeatureLock = ({ 
  feature, 
  message, 
  requiredPlan = 'pro',
  variant = 'card', // 'card', 'inline', 'overlay', 'banner'
  showCTA = true,
  children 
}) => {
  const navigate = useNavigate();

  const getPlanIcon = () => {
    if (requiredPlan === 'business') return <Zap className="w-6 h-6" />;
    if (requiredPlan === 'pro') return <Crown className="w-6 h-6" />;
    return <Lock className="w-6 h-6" />;
  };

  const getPlanColor = () => {
    if (requiredPlan === 'business') return {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      text: 'text-purple-900',
      button: 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600'
    };
    if (requiredPlan === 'pro') return {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      text: 'text-orange-900',
      button: 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600'
    };
    return {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-900',
      button: 'bg-blue-500 hover:bg-blue-600'
    };
  };

  const colors = getPlanColor();
  const icon = getPlanIcon();

  // Variant: Card (bloc complet)
  if (variant === 'card') {
    return (
      <div className={`${colors.bg} ${colors.border} border-2 rounded-xl p-8 text-center`}>
        <div className={`${colors.text} mx-auto mb-4 w-16 h-16 rounded-full bg-white/50 flex items-center justify-center`}>
          {icon}
        </div>
        <h3 className={`text-xl font-bold ${colors.text} mb-2`}>
          Fonctionnalité Premium
        </h3>
        <p className="text-gray-700 mb-6">
          {message || `Cette fonctionnalité nécessite le plan ${requiredPlan.toUpperCase()}`}
        </p>
        {showCTA && (
          <Button
            onClick={() => navigate('/dashboard/subscriptions')}
            className={`${colors.button} text-white border-0`}
          >
            Voir les Plans
            <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
        )}
      </div>
    );
  }

  // Variant: Inline (message compact)
  if (variant === 'inline') {
    return (
      <div className={`${colors.bg} ${colors.border} border rounded-lg p-4 flex items-center gap-3`}>
        <div className={colors.text}>
          {icon}
        </div>
        <div className="flex-1">
          <p className={`text-sm ${colors.text} font-medium`}>
            {message || `Plan ${requiredPlan.toUpperCase()} requis`}
          </p>
        </div>
        {showCTA && (
          <Button
            size="sm"
            onClick={() => navigate('/dashboard/subscriptions')}
            className={`${colors.button} text-white border-0`}
          >
            Upgrade
          </Button>
        )}
      </div>
    );
  }

  // Variant: Overlay (superposition sur le contenu)
  if (variant === 'overlay') {
    return (
      <div className="relative">
        {/* Contenu original flouté */}
        <div className="blur-sm opacity-50 pointer-events-none">
          {children}
        </div>
        {/* Overlay de verrouillage */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={`${colors.bg} ${colors.border} border-2 rounded-xl p-6 text-center max-w-md shadow-xl`}>
            <div className={`${colors.text} mx-auto mb-3 w-12 h-12 rounded-full bg-white/50 flex items-center justify-center`}>
              {icon}
            </div>
            <p className={`text-sm ${colors.text} mb-4 font-medium`}>
              {message || `Plan ${requiredPlan.toUpperCase()} requis`}
            </p>
            {showCTA && (
              <Button
                size="sm"
                onClick={() => navigate('/dashboard/subscriptions')}
                className={`${colors.button} text-white border-0`}
              >
                Voir les Plans
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Variant: Banner (bandeau en haut)
  if (variant === 'banner') {
    return (
      <div className={`${colors.bg} ${colors.border} border-l-4 rounded-lg p-4 mb-6`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={colors.text}>
              {icon}
            </div>
            <p className={`text-sm ${colors.text} font-medium`}>
              {message || `Cette fonctionnalité nécessite le plan ${requiredPlan.toUpperCase()}`}
            </p>
          </div>
          {showCTA && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => navigate('/dashboard/subscriptions')}
              className={`${colors.text} hover:bg-white/50`}
            >
              Voir les Plans
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    );
  }

  return null;
};

export default FeatureLock;
