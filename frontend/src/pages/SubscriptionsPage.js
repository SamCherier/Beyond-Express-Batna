import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { 
  getAllPlans, 
  getMySubscription, 
  subscribeToPlan, 
  cancelSubscription, 
  upgradeSubscription 
} from '@/api';
import { Check, Crown, Zap, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const SubscriptionsPage = () => {
  const { t, i18n } = useTranslation();
  const { user } = useContext(AuthContext);
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedBillingPeriod, setSelectedBillingPeriod] = useState('monthly');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [plansRes, subRes] = await Promise.all([
        getAllPlans(),
        getMySubscription()
      ]);
      
      setPlans(plansRes.data.plans || []);
      setCurrentSubscription(subRes.data.subscription || null);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planType) => {
    try {
      setActionLoading(true);
      await subscribeToPlan(planType, selectedBillingPeriod);
      toast.success('Abonnement créé avec succès!');
      await fetchData();
    } catch (error) {
      console.error('Error subscribing:', error);
      toast.error('Erreur lors de l\'abonnement');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpgrade = async (newPlanType) => {
    try {
      setActionLoading(true);
      await upgradeSubscription(newPlanType, selectedBillingPeriod);
      toast.success('Plan mis à jour avec succès!');
      await fetchData();
    } catch (error) {
      console.error('Error upgrading:', error);
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Êtes-vous sûr de vouloir annuler votre abonnement?')) {
      return;
    }

    try {
      setActionLoading(true);
      await cancelSubscription('Annulation demandée par l\'utilisateur');
      toast.success('Abonnement annulé. Vous êtes maintenant sur le plan FREE.');
      await fetchData();
    } catch (error) {
      console.error('Error cancelling:', error);
      toast.error('Erreur lors de l\'annulation');
    } finally {
      setActionLoading(false);
    }
  };

  const getLocalizedName = (plan) => {
    const lang = i18n.language;
    if (lang === 'ar') return plan.name_ar;
    if (lang === 'en') return plan.name_en;
    return plan.name_fr;
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('fr-DZ', {
      style: 'currency',
      currency: 'DZD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price);
  };

  const getPriceForPeriod = (plan, period) => {
    const pricing = plan.pricing;
    switch (period) {
      case 'quarterly':
        return pricing.quarterly_price || pricing.monthly_price * 3;
      case 'biannual':
        return pricing.biannual_price || pricing.monthly_price * 6;
      case 'annual':
        return pricing.annual_price || pricing.monthly_price * 12;
      default:
        return pricing.monthly_price;
    }
  };

  const billingPeriods = [
    { value: 'monthly', label: 'Mensuel', months: 1 },
    { value: 'quarterly', label: 'Trimestriel (-10%)', months: 3 },
    { value: 'biannual', label: 'Semestriel (-15%)', months: 6 },
    { value: 'annual', label: 'Annuel (-20%)', months: 12 }
  ];

  const currentPlanType = user?.current_plan || 'free';

  if (loading) {
    return (
      <div className="p-8">
        <div className="text-center">
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-hacen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Hacen Tunisia Bd, sans-serif' }}>
            Gérer mon Abonnement
          </h1>
          <p className="text-gray-600">
            Plan actuel: <span className="font-bold text-red-500">{currentPlanType.toUpperCase()}</span>
          </p>
        </div>

        {/* Current Subscription Info */}
        {currentSubscription && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border-l-4 border-red-500">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Abonnement Actif
                </h3>
                <p className="text-gray-600">
                  Plan: {currentSubscription.plan_type.toUpperCase()}
                </p>
                <p className="text-gray-600">
                  Période: {currentSubscription.billing_period}
                </p>
                <p className="text-gray-600">
                  Expire le: {new Date(currentSubscription.end_date).toLocaleDateString('fr-FR')}
                </p>
              </div>
              <Button
                onClick={handleCancel}
                disabled={actionLoading}
                variant="destructive"
                className="flex items-center gap-2"
              >
                <X className="w-4 h-4" />
                Annuler l'abonnement
              </Button>
            </div>
          </div>
        )}

        {/* Billing Period Selector */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Période de facturation
          </h3>
          <div className="grid grid-cols-4 gap-4">
            {billingPeriods.map((period) => (
              <button
                key={period.value}
                onClick={() => setSelectedBillingPeriod(period.value)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedBillingPeriod === period.value
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-center">
                  <p className="font-bold text-gray-900">{period.label}</p>
                  <p className="text-sm text-gray-600">{period.months} mois</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Plans Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => {
            const isCurrentPlan = currentPlanType === plan.plan_type;
            const price = getPriceForPeriod(plan, selectedBillingPeriod);
            const isPro = plan.plan_type === 'pro';
            const isBusiness = plan.plan_type === 'business';

            return (
              <div
                key={plan.id}
                className={`relative bg-white rounded-xl shadow-lg p-6 transition-all ${
                  isCurrentPlan ? 'border-2 border-green-500' : 'border border-gray-200'
                } ${isPro ? 'lg:scale-105' : ''}`}
              >
                {/* Current Plan Badge */}
                {isCurrentPlan && (
                  <div className="absolute top-0 right-0 bg-green-500 text-white px-3 py-1 rounded-bl-xl rounded-tr-xl text-sm font-bold">
                    <Check className="w-4 h-4 inline mr-1" />
                    Plan Actuel
                  </div>
                )}

                {/* Plan Icon */}
                <div className="mb-4">
                  {isPro && <Crown className="w-8 h-8 text-orange-500" />}
                  {isBusiness && <Zap className="w-8 h-8 text-purple-500" />}
                </div>

                {/* Plan Name */}
                <h3 className="text-2xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Hacen Tunisia Bd, sans-serif' }}>
                  {getLocalizedName(plan)}
                </h3>

                {/* Price */}
                <div className="mb-6">
                  {price === 0 ? (
                    <div className="text-3xl font-bold text-gray-900">FREE</div>
                  ) : (
                    <>
                      <div className="text-3xl font-bold text-gray-900">
                        {formatPrice(price)}
                      </div>
                      <p className="text-sm text-gray-600">
                        pour {billingPeriods.find(p => p.value === selectedBillingPeriod)?.months} mois
                      </p>
                    </>
                  )}
                </div>

                {/* Key Features */}
                <div className="space-y-2 mb-6">
                  <div className="flex items-center gap-2 text-gray-700">
                    <Check className="w-4 h-4 text-green-500" />
                    <span className="text-sm">
                      {plan.features.max_orders_per_month === -1 
                        ? 'Commandes illimitées' 
                        : `${plan.features.max_orders_per_month} commandes/mois`
                      }
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-700">
                    <Check className="w-4 h-4 text-green-500" />
                    <span className="text-sm">
                      {plan.features.unlimited_delivery_companies
                        ? 'Transporteurs illimités'
                        : `${plan.features.max_delivery_companies} transporteur(s)`
                      }
                    </span>
                  </div>
                  {plan.features.whatsapp_auto_confirmation && (
                    <div className="flex items-center gap-2 text-gray-700">
                      <Check className="w-4 h-4 text-green-500" />
                      <span className="text-sm">WhatsApp Auto</span>
                    </div>
                  )}
                  {plan.features.pro_dashboard && (
                    <div className="flex items-center gap-2 text-gray-700">
                      <Check className="w-4 h-4 text-green-500" />
                      <span className="text-sm">Dashboard Pro</span>
                    </div>
                  )}
                </div>

                {/* Action Button */}
                {!isCurrentPlan && (
                  <Button
                    onClick={() => currentSubscription ? handleUpgrade(plan.plan_type) : handleSubscribe(plan.plan_type)}
                    disabled={actionLoading}
                    className="w-full"
                    variant={isPro || isBusiness ? 'default' : 'outline'}
                  >
                    {currentSubscription ? 'Changer de plan' : 'Souscrire'}
                  </Button>
                )}
              </div>
            );
          })}
        </div>

        {/* Info Banner */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-blue-500 flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-bold text-blue-900 mb-2">Information importante</h4>
              <p className="text-blue-800 text-sm">
                • Les changements de plan prennent effet immédiatement<br />
                • Période d'essai gratuite de 7 jours pour tous les nouveaux abonnements<br />
                • Facturation mensuelle, trimestrielle, semestrielle ou annuelle disponible<br />
                • Mode SIMULATION: Aucun paiement réel n'est effectué pour le moment
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionsPage;
