import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { Package, Truck, MessageCircle, Brain, Zap, Shield, ChevronRight, Sparkles, TrendingUp } from 'lucide-react';
import BeyondExpressLogo from '@/components/BeyondExpressLogo';
import ThemeToggle from '@/components/ThemeToggle';

const LandingPageModernV2 = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  
  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  const aiFeatures = [
    {
      icon: Brain,
      title: "AI Reconciliation",
      description: "Réconciliation financière automatisée avec IA. Fini les erreurs de comptabilité.",
      gradient: "from-purple-500 to-pink-500"
    },
    {
      icon: Zap,
      title: "Smart Routing",
      description: "Optimisation intelligente des routes de livraison pour réduire les coûts et les délais.",
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      icon: MessageCircle,
      title: "WhatsApp Bot",
      description: "Support client automatique 24/7. Réponses instantanées à vos clients.",
      gradient: "from-green-500 to-emerald-500"
    }
  ];

  const partners = [
    { name: 'Yalidine', logo: '🚚' },
    { name: 'ZR Express', logo: '📦' },
    { name: 'Procolis', logo: '🎯' },
    { name: 'Maystro', logo: '⚡' }
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
              <BeyondExpressLogo size="sm" />
              <span className="text-xl font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Hacen Tunisia, serif' }}>
                Beyond Express
              </span>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/tracking')}
                className="text-gray-700 dark:text-gray-300 hover:text-red-500 dark:hover:text-red-400 flex items-center gap-2"
              >
                <Package className="w-4 h-4" />
                Suivre un Colis
              </Button>

              <ThemeToggle />

              <div className="hidden md:flex gap-2">
                <button
                  onClick={() => changeLanguage('fr')}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                    i18n.language === 'fr' 
                      ? 'bg-red-500 text-white' 
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  FR
                </button>
                <button
                  onClick={() => changeLanguage('ar')}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                    i18n.language === 'ar' 
                      ? 'bg-red-500 text-white' 
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  AR
                </button>
                <button
                  onClick={() => changeLanguage('en')}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                    i18n.language === 'en' 
                      ? 'bg-red-500 text-white' 
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  EN
                </button>
              </div>

              <Button
                variant="ghost"
                onClick={() => navigate('/login')}
                className="text-gray-700 dark:text-gray-300"
              >
                Connexion
              </Button>
              <Button
                onClick={() => navigate('/register')}
                className="bg-red-500 hover:bg-red-600 text-white"
              >
                Commencer
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 relative overflow-hidden">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-red-50 via-orange-50 to-pink-50 dark:from-gray-900 dark:via-red-950/20 dark:to-gray-900 -z-10" />
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px] -z-10" />

        <div className="container mx-auto text-center max-w-5xl">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-100 dark:bg-red-950/30 text-red-600 dark:text-red-400 text-sm font-medium mb-8 border border-red-200 dark:border-red-900">
            <Sparkles className="w-4 h-4" />
            Powered by AI
          </div>

          <h1 className="text-6xl lg:text-8xl font-bold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-gray-900 via-red-600 to-orange-600 dark:from-white dark:via-red-400 dark:to-orange-400 bg-clip-text text-transparent">
              La Logistique
            </span>
            <br />
            <span className="bg-gradient-to-r from-orange-600 via-red-600 to-pink-600 dark:from-orange-400 dark:via-red-400 dark:to-pink-400 bg-clip-text text-transparent">
              Intelligente
            </span>
          </h1>

          <p className="text-2xl text-gray-600 dark:text-gray-400 mb-4 max-w-3xl mx-auto" style={{ fontFamily: 'Hacen Tunisia, serif', lineHeight: '1.8' }}>
            خليك مركز على البيع، احنا نديرولك التوصيل
          </p>

          <p className="text-lg text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
            La première plateforme algérienne de logistique automatisée par IA. Gérez vos commandes, optimisez vos livraisons, boostez votre business.
          </p>

          <div className="flex flex-col items-center gap-4">
            <div className="flex gap-4">
              <Button
                size="lg"
                onClick={() => navigate('/register')}
                className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white text-lg px-8 py-6 rounded-xl shadow-lg hover:shadow-xl transition-all group"
              >
                Commencer Gratuitement
                <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate('/login')}
                className="border-2 border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 text-lg px-8 py-6 rounded-xl"
              >
                Se Connecter
              </Button>
            </div>

            <button
              onClick={() => navigate('/tracking')}
              className="text-gray-600 dark:text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors flex items-center gap-2 text-sm group"
            >
              <Package className="w-4 h-4 group-hover:text-red-500 dark:group-hover:text-red-400 transition-colors" />
              <span>Déjà client ? <span className="underline font-medium">Suivre mon colis</span></span>
            </button>
          </div>
        </div>
      </section>

      {/* AI Showcase Section - Bento Grid */}
      <section className="py-20 px-4 bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-100 dark:bg-purple-950/30 text-purple-600 dark:text-purple-400 text-sm font-medium mb-4">
              <Brain className="w-4 h-4" />
              Intelligence Artificielle
            </div>
            <h2 className="text-5xl font-bold mb-4 text-gray-900 dark:text-white">
              Automatisez Tout
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Notre IA travaille pour vous 24/7
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {aiFeatures.map((feature, index) => (
              <div
                key={index}
                className="group relative bg-white dark:bg-gray-800 rounded-2xl p-8 border border-gray-200 dark:border-gray-700 hover:border-transparent hover:shadow-2xl transition-all duration-300"
              >
                {/* Gradient Border on Hover */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-10 transition-opacity -z-10`} />
                
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-7 h-7 text-white" />
                </div>

                <h3 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  {feature.description}
                </p>

                <div className="mt-6 flex items-center text-red-500 dark:text-red-400 font-medium group-hover:gap-2 gap-1 transition-all">
                  En savoir plus
                  <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div className="p-8">
              <div className="text-5xl font-bold bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent mb-2">
                10,000+
              </div>
              <p className="text-gray-600 dark:text-gray-400 font-medium">Commandes Traitées</p>
            </div>
            <div className="p-8">
              <div className="text-5xl font-bold bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent mb-2">
                500+
              </div>
              <p className="text-gray-600 dark:text-gray-400 font-medium">Marchands Actifs</p>
            </div>
            <div className="p-8">
              <div className="text-5xl font-bold bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent mb-2">
                99.2%
              </div>
              <p className="text-gray-600 dark:text-gray-400 font-medium">Taux de Livraison</p>
            </div>
          </div>
        </div>
      </section>

      {/* Partners Section */}
      <section className="py-20 px-4 bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto max-w-6xl text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-8 uppercase tracking-wider">
            Intégré avec les meilleurs
          </p>
          <div className="flex flex-wrap justify-center items-center gap-12">
            {partners.map((partner, index) => (
              <div
                key={index}
                className="group flex flex-col items-center gap-2 grayscale hover:grayscale-0 transition-all duration-300 cursor-pointer"
              >
                <div className="text-5xl group-hover:scale-110 transition-transform">
                  {partner.logo}
                </div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
                  {partner.name}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-red-500 via-orange-500 to-pink-500 dark:from-red-600 dark:via-orange-600 dark:to-pink-600 -z-10" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff0a_1px,transparent_1px),linear-gradient(to_bottom,#ffffff0a_1px,transparent_1px)] bg-[size:20px_20px] -z-10" />

        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="text-5xl font-bold text-white mb-6">
            Prêt à Transformer Votre Business ?
          </h2>
          <p className="text-xl text-white/90 mb-10 max-w-2xl mx-auto">
            Rejoignez des centaines de marchands qui ont automatisé leur logistique avec Beyond Express.
          </p>
          <Button
            size="lg"
            onClick={() => navigate('/register')}
            className="bg-white text-red-500 hover:bg-gray-100 text-lg px-10 py-6 rounded-xl shadow-2xl"
          >
            Démarrer Gratuitement
            <Sparkles className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800 py-12 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <BeyondExpressLogo size="sm" />
              <span className="font-bold text-gray-900 dark:text-white" style={{ fontFamily: 'Hacen Tunisia, serif' }}>
                Beyond Express
              </span>
            </div>
            
            <div className="flex gap-8 text-sm text-gray-600 dark:text-gray-400">
              <button onClick={() => navigate('/tracking')} className="hover:text-red-500 dark:hover:text-red-400 transition-colors">
                Suivre un Colis
              </button>
              <button onClick={() => navigate('/login')} className="hover:text-red-500 dark:hover:text-red-400 transition-colors">
                Se Connecter
              </button>
              <button onClick={() => navigate('/register')} className="hover:text-red-500 dark:hover:text-red-400 transition-colors">
                S'inscrire
              </button>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-800 text-center text-sm text-gray-500 dark:text-gray-400">
            © 2025 Beyond Express - Plateforme de Livraison Algérienne
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPageModernV2;
