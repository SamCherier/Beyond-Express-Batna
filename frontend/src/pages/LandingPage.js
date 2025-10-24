import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import AnimatedLogo from '@/components/AnimatedLogo';
import { Package, Warehouse, Truck, Globe, Shield, Zap } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  const services = [
    {
      icon: <Warehouse className="w-12 h-12" />,
      title: t('storage'),
      description: 'Stockage sécurisé et optimisé pour vos produits'
    },
    {
      icon: <Package className="w-12 h-12" />,
      title: t('fulfillment'),
      description: 'Préparation rapide et précise de vos commandes'
    },
    {
      icon: <Truck className="w-12 h-12" />,
      title: t('shipping'),
      description: 'Livraison multi-transporteurs partout en Algérie'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-red-50" data-testid="landing-page">
      {/* Header */}
      <header className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <AnimatedLogo size="sm" />
            <span className="text-2xl font-bold text-gray-900" style={{ fontFamily: 'Brockmann, sans-serif' }}>
              Beyond Express
            </span>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Language Switcher */}
            <div className="flex gap-2">
              <button
                onClick={() => changeLanguage('fr')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'fr' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                data-testid="lang-fr"
              >
                FR
              </button>
              <button
                onClick={() => changeLanguage('ar')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'ar' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                data-testid="lang-ar"
              >
                AR
              </button>
              <button
                onClick={() => changeLanguage('en')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'en' ? 'bg-red-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                data-testid="lang-en"
              >
                EN
              </button>
            </div>
            
            <Button
              variant="ghost"
              onClick={() => navigate('/login')}
              data-testid="login-button"
              className="hover:bg-red-50 hover:text-red-600"
            >
              {t('login')}
            </Button>
            <Button
              onClick={() => navigate('/register')}
              data-testid="register-button"
              className="bg-red-500 hover:bg-red-600 text-white"
            >
              {t('register')}
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <div className="flex-1 space-y-6">
              <h1 
                className="text-5xl lg:text-6xl font-bold text-gray-900 leading-tight"
                style={{ fontFamily: 'EB Garamond, serif' }}
                data-testid="hero-title"
              >
                {t('heroTitle')}
              </h1>
              <p className="text-xl text-gray-600" style={{ fontFamily: 'Fira Sans, sans-serif' }}>
                {t('heroSubtitle')}
              </p>
              <div className="flex gap-4 pt-4">
                <Button
                  size="lg"
                  onClick={() => navigate('/register')}
                  data-testid="get-started-btn"
                  className="bg-red-500 hover:bg-red-600 text-white text-lg px-8 py-6 rounded-full shadow-lg hover:shadow-xl transition-all"
                >
                  {t('getStarted')}
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => navigate('/login')}
                  className="border-2 border-red-500 text-red-500 hover:bg-red-50 text-lg px-8 py-6 rounded-full"
                >
                  {t('login')}
                </Button>
              </div>
            </div>
            
            <div className="flex-1 flex justify-center">
              <AnimatedLogo size="xl" />
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4 max-w-6xl">
          <h2 
            className="text-4xl font-bold text-center mb-12 text-gray-900"
            style={{ fontFamily: 'EB Garamond, serif' }}
          >
            {t('services')}
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {services.map((service, index) => (
              <div
                key={index}
                className="group p-8 rounded-2xl bg-gradient-to-br from-white to-red-50 border border-red-100 hover:shadow-xl transition-all duration-300 hover:-translate-y-2"
                data-testid={`service-${index}`}
              >
                <div className="text-red-500 mb-4 group-hover:scale-110 transition-transform">
                  {service.icon}
                </div>
                <h3 className="text-2xl font-bold mb-2 text-gray-900">{service.title}</h3>
                <p className="text-gray-600">{service.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gradient-to-br from-red-50 to-white">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <Globe className="w-16 h-16 mx-auto mb-4 text-red-500" />
              <h3 className="text-xl font-bold mb-2">Multi-langues</h3>
              <p className="text-gray-600">Français, Arabe, Anglais</p>
            </div>
            <div className="text-center p-6">
              <Shield className="w-16 h-16 mx-auto mb-4 text-red-500" />
              <h3 className="text-xl font-bold mb-2">Sécurisé</h3>
              <p className="text-gray-600">Authentification renforcée</p>
            </div>
            <div className="text-center p-6">
              <Zap className="w-16 h-16 mx-auto mb-4 text-red-500" />
              <h3 className="text-xl font-bold mb-2">Assistant IA</h3>
              <p className="text-gray-600">Support intelligent 24/7</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-xl">B</span>
                </div>
                <span className="text-xl font-bold">Beyond Express</span>
              </div>
              <p className="text-gray-400">City 84 centre-ville Batna, Batna, Algeria</p>
            </div>
            <div>
              <h4 className="font-bold mb-4">Contact</h4>
              <p className="text-gray-400">Email: contact@beyondexpress.com</p>
              <p className="text-gray-400">Web: beyond.express.dz</p>
            </div>
            <div>
              <h4 className="font-bold mb-4">Réseaux Sociaux</h4>
              <p className="text-gray-400">Instagram: @beyond.express</p>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2025 Beyond Express. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;