import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import GlitchLogo from '@/components/GlitchLogo';
import ThreeDBackground from '@/components/ThreeDBackground';
import PricingSection from '@/components/PricingSection';
import { Package, Warehouse, Truck, Shield, Brain, AlertCircle, Zap, Cpu, Globe } from 'lucide-react';

const LandingPageFuturistic = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  const features = [
    {
      icon: <Package className="w-8 h-8" />,
      title: t('orderManagement'),
      description: "Gestion intelligente des commandes avec IA",
      color: "from-red-500 to-orange-500"
    },
    {
      icon: <Warehouse className="w-8 h-8" />,
      title: t('stockManagement'),
      description: "Inventaire en temps réel",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: <Truck className="w-8 h-8" />,
      title: t('deliveryTracking'),
      description: "Suivi en temps réel via 13+ partenaires",
      color: "from-cyan-500 to-blue-500"
    },
    {
      icon: <Brain className="w-8 h-8" />,
      title: "IA Avancée",
      description: "Score de risque et prédictions",
      color: "from-green-500 to-emerald-500"
    }
  ];

  return (
    <div className="min-h-screen bg-black text-white overflow-hidden">
      {/* 3D Background */}
      <ThreeDBackground />

      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 backdrop-blur-md bg-black/30 border-b border-red-500/20">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <GlitchLogo size="medium" />
          
          <div className="flex items-center gap-6">
            {/* Language Selector */}
            <div className="flex gap-2">
              {['fr', 'ar', 'en'].map((lng) => (
                <button
                  key={lng}
                  onClick={() => changeLanguage(lng)}
                  className={`px-3 py-1 rounded-lg text-sm font-bold uppercase transition-all ${
                    i18n.language === lng
                      ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white'
                      : 'bg-gray-800/50 text-gray-400 hover:text-white hover:bg-gray-700/50'
                  }`}
                >
                  {lng}
                </button>
              ))}
            </div>

            <Button
              onClick={() => navigate('/login')}
              className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white font-bold px-6 py-2 rounded-lg shadow-lg shadow-red-500/50 transition-all hover:scale-105"
            >
              {t('login')}
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4">
        <div className="container mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <div className="mb-6 flex justify-center">
              <GlitchLogo size="xlarge" />
            </div>
            
            <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">
              <span className="bg-gradient-to-r from-red-500 via-orange-500 to-red-500 bg-clip-text text-transparent animate-gradient">
                L'Avenir de la Logistique
              </span>
              <br />
              <span className="text-white">en Algérie</span>
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-300 mb-4">
              {t('landingSubtitle') || 'خليك مركز على البيع، إحنا نتكلفو بالباقي'}
            </p>
            
            <p className="text-lg text-cyan-400 font-semibold mb-8 flex items-center justify-center gap-2">
              <Zap className="w-5 h-5" />
              Propulsé par l'Intelligence Artificielle
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                onClick={() => navigate('/register')}
                className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white font-bold px-8 py-4 text-lg rounded-xl shadow-2xl shadow-red-500/50 transition-all hover:scale-105 hover:shadow-red-500/80"
              >
                Commencer Gratuitement
              </Button>
              
              <Button
                onClick={() => navigate('/login')}
                variant="outline"
                className="border-2 border-cyan-500 text-cyan-400 hover:bg-cyan-500/10 font-bold px-8 py-4 text-lg rounded-xl transition-all hover:scale-105"
              >
                Découvrir la Démo
              </Button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20">
            {[
              { value: '13+', label: 'Partenaires de Livraison', icon: <Truck /> },
              { value: '48', label: 'Wilayas Couvertes', icon: <Globe /> },
              { value: '99%', label: 'Disponibilité', icon: <Shield /> },
              { value: 'AI', label: 'Intelligence Artificielle', icon: <Brain /> }
            ].map((stat, idx) => (
              <div
                key={idx}
                className="relative group p-6 rounded-2xl bg-gradient-to-br from-gray-900/50 to-black/50 border border-red-500/20 backdrop-blur-sm hover:border-red-500/50 transition-all hover:scale-105"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-red-500/10 to-orange-500/10 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative z-10">
                  <div className="text-cyan-400 mb-2">{stat.icon}</div>
                  <div className="text-4xl font-bold bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent mb-2">
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-400">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 relative">
        <div className="container mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-bold mb-4">
              <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                Technologies du Futur
              </span>
            </h2>
            <p className="text-xl text-gray-400">Des outils surpuissants pour votre business</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, idx) => (
              <div
                key={idx}
                className="group relative p-8 rounded-2xl bg-gradient-to-br from-gray-900/80 to-black/80 border border-gray-700/50 backdrop-blur-sm hover:border-cyan-500/50 transition-all duration-300 hover:scale-105 overflow-hidden"
              >
                {/* Glow effect */}
                <div className={`absolute inset-0 bg-gradient-to-r ${feature.color} opacity-0 group-hover:opacity-20 transition-opacity blur-xl`} />
                
                <div className="relative z-10">
                  <div className={`w-16 h-16 rounded-xl bg-gradient-to-r ${feature.color} flex items-center justify-center mb-4 shadow-lg`}>
                    {feature.icon}
                  </div>
                  
                  <h3 className="text-xl font-bold text-white mb-2">
                    {feature.title}
                  </h3>
                  
                  <p className="text-gray-400 text-sm">
                    {feature.description}
                  </p>
                </div>

                {/* Scan line effect */}
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-0 group-hover:opacity-100 group-hover:animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <PricingSection />

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-4xl">
          <div className="relative p-12 rounded-3xl bg-gradient-to-r from-red-500/20 to-orange-500/20 border border-red-500/30 backdrop-blur-md overflow-hidden">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48cGF0dGVybiBpZD0iZ3JpZCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBwYXR0ZXJuVW5pdHM9InVzZXJTcGFjZU9uVXNlIj48cGF0aCBkPSJNIDQwIDAgTCAwIDAgMCA0MCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwwLDAsMC4xKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-30" />
            
            <div className="relative z-10 text-center">
              <h2 className="text-4xl font-bold mb-4 text-white">
                Prêt à Révolutionner Votre Logistique ?
              </h2>
              <p className="text-xl text-gray-300 mb-8">
                Rejoignez les entreprises qui font confiance à Beyond Express
              </p>
              
              <Button
                onClick={() => navigate('/register')}
                className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white font-bold px-12 py-6 text-xl rounded-xl shadow-2xl shadow-red-500/50 transition-all hover:scale-110"
              >
                <Zap className="w-6 h-6 mr-2" />
                Commencer Maintenant
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 px-4 backdrop-blur-md bg-black/50">
        <div className="container mx-auto max-w-7xl text-center">
          <div className="mb-4">
            <GlitchLogo size="small" />
          </div>
          <p className="text-gray-500 text-sm">
            © 2025 Beyond Express. Powered by AI. Made in Algeria 🇩🇿
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPageFuturistic;
