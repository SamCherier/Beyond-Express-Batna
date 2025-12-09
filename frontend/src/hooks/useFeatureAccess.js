import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { checkFeatureLimit } from '@/api';

/**
 * Hook pour vérifier l'accès aux fonctionnalités basé sur le plan de l'utilisateur
 * 
 * Utilisation:
 * const { hasAccess, limit, currentUsage, checkAccess } = useFeatureAccess();
 * 
 * const canAddOrder = checkAccess('orders');
 * const canUseWhatsApp = checkAccess('whatsapp');
 */
export const useFeatureAccess = () => {
  const { user } = useAuth();
  const [featureLimits, setFeatureLimits] = useState({});

  // Définir les limites par défaut basées sur le plan
  const planLimits = {
    free: {
      max_orders_per_month: 50,  // Total during 7-day trial
      max_delivery_companies: 1,
      max_connected_pages: 1,
      stock_management: false,
      whatsapp_auto_confirmation: false,
      ai_content_generator: false,
      ai_generator_uses: 0,
      advanced_analytics: false,
      pro_dashboard: false,
      unlimited_delivery_companies: false,
      package_tracking: true,
      detailed_reports: false,
      dedicated_account_manager: false,
      preferred_partner_rates: false,
      daily_pickup: false
    },
    beginner: {
      max_orders_per_month: 100,
      max_delivery_companies: 1,
      max_connected_pages: 1,
      stock_management: true,
      whatsapp_auto_confirmation: false,
      ai_content_generator: false,
      ai_generator_uses: 0,
      advanced_analytics: false,
      pro_dashboard: false,  // Dashboard simplifié
      unlimited_delivery_companies: false,
      package_tracking: true,
      detailed_reports: false,
      dedicated_account_manager: false,
      preferred_partner_rates: false,
      daily_pickup: false,
      preparations_included: 50,
      pickups_per_week: 2
    },
    starter: {
      max_orders_per_month: 500,
      max_delivery_companies: 3,
      max_connected_pages: 2,
      stock_management: true,
      whatsapp_auto_confirmation: true,
      ai_content_generator: true,
      ai_generator_uses: 2,  // 2 AI tools only
      advanced_analytics: false,
      pro_dashboard: false,
      unlimited_delivery_companies: false,
      package_tracking: true,
      detailed_reports: false,
      dedicated_account_manager: false,
      preferred_partner_rates: false,
      daily_pickup: false,
      preparations_included: 200,
      pickups_per_week: 4
    },
    pro: {
      max_orders_per_month: -1,  // Unlimited
      max_delivery_companies: -1,  // Unlimited
      max_connected_pages: -1,
      stock_management: true,
      whatsapp_auto_confirmation: true,
      ai_content_generator: true,
      ai_generator_uses: -1,  // Unlimited
      advanced_analytics: true,
      pro_dashboard: true,
      unlimited_delivery_companies: true,
      package_tracking: true,
      detailed_reports: true,
      dedicated_account_manager: true,
      preferred_partner_rates: true,
      daily_pickup: true,
      preparations_included: -1,
      pickups_per_week: 7
    }
  };

  const currentPlan = user?.current_plan || 'free';

  /**
   * Vérifie si l'utilisateur a accès à une fonctionnalité
   * @param {string} feature - Nom de la fonctionnalité (ex: 'whatsapp', 'pro_dashboard', 'orders')
   * @returns {boolean} - True si l'utilisateur a accès
   */
  const checkAccess = (feature) => {
    const limits = planLimits[currentPlan] || planLimits.free;
    
    // Pour les features booléennes
    if (typeof limits[feature] === 'boolean') {
      return limits[feature];
    }
    
    // Pour les features avec limites numériques
    if (typeof limits[feature] === 'number') {
      return limits[feature] !== 0;
    }
    
    return false;
  };

  /**
   * Obtient la limite pour une fonctionnalité spécifique
   * @param {string} feature - Nom de la fonctionnalité
   * @returns {number|boolean} - La limite ou le statut d'accès
   */
  const getLimit = (feature) => {
    const limits = planLimits[currentPlan] || planLimits.free;
    return limits[feature] !== undefined ? limits[feature] : false;
  };

  /**
   * Vérifie si une limite est atteinte
   * @param {string} feature - Nom de la fonctionnalité
   * @param {number} currentCount - Nombre actuel d'utilisation
   * @returns {boolean} - True si la limite est atteinte
   */
  const isLimitReached = (feature, currentCount) => {
    const limit = getLimit(feature);
    if (typeof limit === 'number') {
      if (limit === -1) return false; // Illimité
      return currentCount >= limit;
    }
    return !limit; // Si c'est un booléen, retourne l'inverse (pas d'accès = limite atteinte)
  };

  /**
   * Obtient le nom du plan requis pour une fonctionnalité
   * @param {string} feature - Nom de la fonctionnalité
   * @returns {string} - Nom du plan requis (starter, pro, business)
   */
  const getRequiredPlan = (feature) => {
    // Vérifier dans l'ordre: starter -> pro -> business
    if (planLimits.starter[feature]) return 'starter';
    if (planLimits.pro[feature]) return 'pro';
    if (planLimits.business[feature]) return 'business';
    return 'pro'; // Par défaut
  };

  /**
   * Obtient un message d'upgrade personnalisé
   * @param {string} feature - Nom de la fonctionnalité
   * @returns {string} - Message d'upgrade
   */
  const getUpgradeMessage = (feature) => {
    const requiredPlan = getRequiredPlan(feature);
    const featureNames = {
      whatsapp_auto_confirmation: 'la Confirmation WhatsApp automatique',
      pro_dashboard: 'le Dashboard Professionnel',
      ai_content_generator: 'le Générateur de Contenu IA',
      advanced_analytics: 'les Analytiques Avancées',
      stock_management: 'la Gestion de Stock',
      detailed_reports: 'les Rapports Détaillés',
      dedicated_account_manager: 'le Gestionnaire de Compte Dédié',
      preferred_partner_rates: 'les Tarifs Préférentiels',
      daily_pickup: 'le Ramassage Quotidien'
    };

    const planNames = {
      starter: 'STARTER',
      pro: 'PRO',
      business: 'BUSINESS'
    };

    const featureName = featureNames[feature] || 'cette fonctionnalité';
    const planName = planNames[requiredPlan] || 'un plan supérieur';

    return `Passez au plan ${planName} pour accéder à ${featureName}`;
  };

  return {
    currentPlan,
    planLimits: planLimits[currentPlan] || planLimits.free,
    checkAccess,
    getLimit,
    isLimitReached,
    getRequiredPlan,
    getUpgradeMessage
  };
};

export default useFeatureAccess;
