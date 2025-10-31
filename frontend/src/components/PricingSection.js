import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Check, Star, Zap } from 'lucide-react';
import { getAllPlans } from '@/api';

const PricingSection = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await getAllPlans();
        setPlans(response.data.plans || []);
      } catch (error) {
        console.error('Error fetching plans:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  const getPlanIcon = (planType) => {
    if (planType === 'pro') return <Star className="w-6 h-6" />;
    if (planType === 'business') return <Zap className="w-6 h-6" />;
    return null;
  };

  const getPlanBadge = (planType) => {
    if (planType === 'pro') return t('mostPopular');
    if (planType === 'business') return t('recommended');
    return null;
  };

  const getLocalizedName = (plan) => {
    const lang = i18n.language;
    if (lang === 'ar') return plan.name_ar;
    if (lang === 'en') return plan.name_en;
    return plan.name_fr;
  };

  const getLocalizedDescription = (plan) => {
    const lang = i18n.language;
    if (lang === 'ar') return plan.description_ar;
    if (lang === 'en') return plan.description_en;
    return plan.description_fr;
  };

  const getLocalizedTarget = (plan) => {
    const lang = i18n.language;
    if (lang === 'ar') return plan.target_audience_ar;
    if (lang === 'en') return plan.target_audience_en;
    return plan.target_audience_fr;
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('fr-DZ', {
      style: 'currency',
      currency: 'DZD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price);
  };

  const getKeyFeatures = (plan) => {
    const features = [];
    
    if (plan.features.max_orders_per_month === -1) {
      features.push(`${t('unlimited')} ${t('ordersPerMonth')}`);
    } else {
      features.push(`${plan.features.max_orders_per_month} ${t('ordersPerMonth')}`);
    }

    if (plan.features.unlimited_delivery_companies) {
      features.push(`${t('unlimited')} ${t('deliveryCompanies')}`);
    } else {
      features.push(`${plan.features.max_delivery_companies} ${t('deliveryCompanies')}`);
    }

    if (plan.features.stock_management) {
      features.push('Gestion de Stock');
    }

    if (plan.features.whatsapp_auto_confirmation) {
      features.push('Confirmation WhatsApp Auto');
    }

    if (plan.features.ai_content_generator) {
      features.push(`Générateur IA (${plan.features.ai_generator_uses} utilisations/mois)`);
    }

    if (plan.features.advanced_analytics) {
      features.push('Analytiques Avancées');
    }

    if (plan.features.pro_dashboard) {
      features.push('Dashboard Professionnel');
    }

    if (plan.features.dedicated_account_manager) {
      features.push('Gestionnaire de Compte Dédié');
    }

    if (plan.features.preferred_partner_rates) {
      features.push('Tarifs Préférentiels Partenaires');
    }

    if (plan.features.daily_pickup) {
      features.push('Ramassage Quotidien');
    }

    if (plan.features.preparations_included > 0) {
      features.push(`${plan.features.preparations_included} Préparations Incluses`);
    }

    if (plan.features.pickups_per_week > 0) {
      features.push(`${plan.features.pickups_per_week} Ramassages/Semaine`);
    }

    return features;
  };

  const getGradientClass = (planType) => {
    switch (planType) {
      case 'free':
        return 'from-gray-500 to-gray-700';
      case 'starter':
        return 'from-blue-500 to-cyan-500';
      case 'pro':
        return 'from-orange-500 to-red-500';
      case 'business':
        return 'from-purple-500 to-pink-500';
      default:
        return 'from-gray-500 to-gray-700';
    }
  };

  if (loading) {
    return (
      <section className="py-24 bg-gradient-to-b from-black to-gray-900">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="text-center text-white">
            <p className="text-xl">{t('loading')}</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-24 bg-gradient-to-b from-black via-gray-900 to-black relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 left-10 w-96 h-96 bg-red-500/5 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="container mx-auto px-4 max-w-7xl relative z-10">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 
            className="text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent font-hacen"
            style={{ fontFamily: 'Hacen Tunisia Bd, Hacen Tunisia, sans-serif' }}
          >
            {t('ourPlans')}
          </h2>
          <p className="text-xl text-gray-400">{t('plansSubtitle')}</p>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {plans.map((plan, index) => {
            const badge = getPlanBadge(plan.plan_type);
            const icon = getPlanIcon(plan.plan_type);
            const gradient = getGradientClass(plan.plan_type);
            const features = getKeyFeatures(plan);
            const isPro = plan.plan_type === 'pro';
            const isBusiness = plan.plan_type === 'business';

            return (
              <div
                key={plan.id}
                className={`relative group rounded-3xl bg-gradient-to-br from-gray-900 to-black border-2 transition-all duration-500 hover:scale-105 overflow-hidden
                  ${isPro || isBusiness ? 'border-red-500/50' : 'border-gray-800'}
                  ${isPro ? 'lg:scale-110 shadow-2xl shadow-red-500/20' : ''}
                `}
              >
                {/* Badge for Popular/Recommended */}
                {badge && (
                  <div className="absolute top-0 right-0 bg-gradient-to-r from-red-500 to-orange-500 text-white px-4 py-2 rounded-bl-2xl rounded-tr-2xl text-sm font-bold flex items-center gap-2">
                    {icon}
                    {badge}
                  </div>
                )}

                {/* Card Content */}
                <div className="p-8">
                  {/* Plan Name */}
                  <div className="mb-4">
                    <h3 className="text-2xl font-bold text-white mb-2 font-hacen">
                      {getLocalizedName(plan)}
                    </h3>
                    <p className="text-gray-400 text-sm min-h-[40px]">
                      {getLocalizedTarget(plan)}
                    </p>
                  </div>

                  {/* Price */}
                  <div className="mb-6">
                    {plan.pricing.monthly_price === 0 ? (
                      <div className="text-4xl font-bold text-white">
                        FREE
                      </div>
                    ) : (
                      <>
                        <div className="text-4xl font-bold text-white">
                          {formatPrice(plan.pricing.monthly_price)}
                        </div>
                        <p className="text-gray-400 text-sm">{t('perMonth')}</p>
                      </>
                    )}
                  </div>

                  {/* Features List */}
                  <div className="mb-8 space-y-3">
                    {features.slice(0, 6).map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <Check className={`w-5 h-5 flex-shrink-0 mt-0.5 text-green-500`} />
                        <span className="text-gray-300 text-sm">{feature}</span>
                      </div>
                    ))}
                  </div>

                  {/* CTA Button */}
                  <button
                    onClick={() => navigate('/register')}
                    className={`w-full py-3 rounded-xl font-bold text-white transition-all duration-300 transform hover:scale-105
                      ${isPro || isBusiness 
                        ? `bg-gradient-to-r ${gradient} hover:shadow-lg hover:shadow-red-500/50` 
                        : 'bg-gray-800 hover:bg-gray-700'
                      }
                    `}
                  >
                    {t('selectPlan')}
                  </button>
                </div>

                {/* Glow Effect for Premium Plans */}
                {(isPro || isBusiness) && (
                  <div className={`absolute -inset-1 bg-gradient-to-r ${gradient} rounded-3xl blur-xl opacity-0 group-hover:opacity-30 transition-opacity duration-500 -z-10`}></div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom Note */}
        <div className="text-center mt-12">
          <p className="text-gray-400 text-sm">
            💳 Tous les packs bénéficient d'une période d'essai gratuite de 7 jours
          </p>
        </div>
      </div>
    </section>
  );
};

export default PricingSection;
