import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import useFeatureAccess from '@/hooks/useFeatureAccess';

/**
 * Composant pour afficher un bandeau avec les limites du plan actuel
 * Affiche uniquement si l'utilisateur est sur le plan FREE
 */
const PlanLimitBanner = () => {
  const navigate = useNavigate();
  const { currentPlan, planLimits } = useFeatureAccess();

  // Ne rien afficher si l'utilisateur n'est pas sur le plan FREE
  if (currentPlan !== 'free') {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-orange-50 to-red-50 border-l-4 border-orange-500 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-orange-900 mb-1">
              Plan GRATUIT - Fonctionnalités Limitées
            </h4>
            <p className="text-sm text-orange-800 mb-2">
              Vous utilisez actuellement le plan BEYOND FREE. Certaines fonctionnalités sont limitées:
            </p>
            <ul className="text-sm text-orange-700 space-y-1 ml-4">
              <li>• Maximum {planLimits.max_orders_per_month} commandes par mois</li>
              <li>• {planLimits.max_delivery_companies} société de livraison uniquement</li>
              <li>• Confirmation WhatsApp automatique désactivée</li>
              <li>• Dashboard Analytics désactivé</li>
              <li>• Assistant IA désactivé</li>
            </ul>
          </div>
        </div>
        <Button
          size="sm"
          onClick={() => navigate('/dashboard/subscriptions')}
          className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white border-0 flex-shrink-0"
        >
          Upgrade
          <ArrowRight className="ml-2 w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

export default PlanLimitBanner;
