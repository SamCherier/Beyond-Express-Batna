import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import BeyondExpressLogo from '@/components/BeyondExpressLogo';
import { Package, Warehouse, Truck, Shield, Brain, AlertCircle } from 'lucide-react';

const LandingPageModern = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  // Services avec traductions
  const services = [
    {
      icon: <Warehouse className="w-16 h-16" />,
      titleKey: 'storageTitle',
      descKey: 'storageDesc',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: <Package className="w-16 h-16" />,
      titleKey: 'fulfillmentTitle',
      descKey: 'fulfillmentDesc',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      icon: <Truck className="w-16 h-16" />,
      titleKey: 'shippingTitle',
      descKey: 'shippingDesc',
      gradient: 'from-orange-500 to-red-500'
    }
  ];

  // Partenaires avec logos
  const deliveryPartners = [
    { name: 'Yalidine', logo: 'logo Yalidine.png' },
    { name: 'DHD', logo: 'logo DHD Livraison.png' },
    { name: 'ZR EXPRESS', logo: 'logo ZR eXPRESS.jpg' },
    { name: 'Maystro', logo: 'logo Maystro Delivery.png' },
    { name: 'EcoTrack', logo: 'logo EcoTrack.png' },
    { name: 'Noest', logo: 'logo Noest.png' },
    { name: 'Guepex', logo: 'logo Guepex.png' },
    { name: 'Kazi Tour', logo: 'logo Kazi Tour.png' },
    { name: 'Lynx Express', logo: 'logo Lynx Express.png' },
    { name: 'DHL', logo: 'logo DHL.png' },
    { name: 'EMS', logo: 'logo EMS.png' },
    { name: 'ARAMEX', logo: 'logo ARAMEX.png' },
    { name: 'ANDERSON', logo: 'logo ANDERSON.png' }
  ];

  // Features IA avec traductions
  const aiFeatures = [
    {
      icon: <Shield className="w-12 h-12" />,
      titleKey: 'riskScoreTitle',
      descKey: 'riskScoreDesc',
      color: 'text-green-500'
    },
    {
      icon: <AlertCircle className="w-12 h-12" />,
      titleKey: 'blacklistTitle',
      descKey: 'blacklistDesc',
      color: 'text-red-500'
    }
  ];
    {
      icon: <AlertCircle className="w-12 h-12" />,
      titleKey: 'blacklistTitle',
      descKey: 'blacklistDesc',
      color: 'text-red-500'
    }
  ];

  const aiModels = [
    { name: 'OpenAI GPT', icon: '🤖' },
    { name: 'Claude', icon: '🧠' },
    { name: 'Gemini', icon: '✨' },
    { name: 'Grok', icon: '⚡' }
  ];

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Fixed Header */}
      <header className="fixed top-0 w-full bg-black/90 backdrop-blur-lg border-b border-red-500/20 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <BeyondExpressLogo size="sm" variant="header" />
            <span className="text-2xl font-bold bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent" style={{ fontFamily: 'Brockmann, sans-serif' }}>
              Beyond Express
            </span>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Language Switcher */}
            <div className="flex gap-2">
              <button
                onClick={() => changeLanguage('fr')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'fr' ? 'bg-red-500 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                FR
              </button>
              <button
                onClick={() => changeLanguage('ar')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'ar' ? 'bg-red-500 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                AR
              </button>
              <button
                onClick={() => changeLanguage('en')}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                  i18n.language === 'en' ? 'bg-red-500 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                EN
              </button>
            </div>
            
            <Button
              variant="ghost"
              onClick={() => navigate('/login')}
              className="text-white hover:bg-red-500/10 hover:text-red-400"
            >
              Connexion
            </Button>
            <Button
              onClick={() => navigate('/register')}
              className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white border-0"
            >
              Commencer
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section with Video Background */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        {/* Video Background */}
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover opacity-40"
        >
          <source src="/videos/intro.mp4" type="video/mp4" />
        </video>
        
        {/* Overlay Gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black"></div>
        
        {/* Hero Content */}
        <div className="relative z-10 container mx-auto px-4 text-center">
          <div className="mb-8">
            <BeyondExpressLogo size="xl" variant="hero" />
          </div>
          
          <h1 
            className="text-6xl lg:text-8xl font-bold mb-6 bg-gradient-to-r from-white via-red-200 to-orange-200 bg-clip-text text-transparent leading-tight"
            style={{ fontFamily: 'EB Garamond, serif' }}
          >
            {t('heroTitle')}
          </h1>
          <p className="text-3xl lg:text-4xl font-bold mb-8 text-red-400" style={{ fontFamily: 'EB Garamond, serif' }}>
            {t('heroSubtitle')}
          </p>
          <p className="text-xl text-gray-300 mb-12 max-w-3xl mx-auto">
            {t('heroDescription')}
          </p>
          
          <div className="flex gap-6 justify-center">
            <Button
              size="lg"
              onClick={() => navigate('/register')}
              className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white text-lg px-10 py-7 rounded-full shadow-2xl hover:shadow-red-500/50 transition-all border-0 transform hover:scale-105"
            >
              {t('getStarted')}
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/login')}
              className="border-2 border-white/30 text-white hover:bg-white/10 text-lg px-10 py-7 rounded-full backdrop-blur-sm"
            >
              {t('loginButton')}
            </Button>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-white/50 rounded-full flex justify-center pt-2">
            <div className="w-1 h-3 bg-white/50 rounded-full"></div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-24 bg-gradient-to-b from-black to-gray-900">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="text-center mb-16">
            <h2 
              className="text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent"
              style={{ fontFamily: 'EB Garamond, serif' }}
            >
              {t('services')}
            </h2>
            <p className="text-xl text-gray-400">{t('servicesSubtitle')}</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {services.map((service, index) => (
              <div
                key={index}
                className="group relative p-8 rounded-3xl bg-gradient-to-br from-gray-900 to-black border border-gray-800 hover:border-red-500/50 transition-all duration-500 hover:scale-105 overflow-hidden"
              >
                {/* Animated Background Gradient */}
                <div className={`absolute inset-0 bg-gradient-to-br ${service.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-500`}></div>
                
                <div className="relative z-10">
                  <div className={`text-white mb-6 group-hover:scale-110 transition-transform duration-300 bg-gradient-to-br ${service.gradient} p-4 rounded-2xl w-fit`}>
                    {service.icon}
                  </div>
                  <h3 className="text-2xl font-bold mb-3 text-white">{t(service.titleKey)}</h3>
                  <p className="text-gray-400">{t(service.descKey)}</p>
                </div>
                
                {/* Glow Effect */}
                <div className="absolute -inset-1 bg-gradient-to-r from-red-500 to-orange-500 rounded-3xl blur-xl opacity-0 group-hover:opacity-20 transition-opacity duration-500"></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Delivery Partners Section */}
      <section className="py-24 bg-gray-900">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="text-center mb-16">
            <h2 
              className="text-5xl font-bold mb-4 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent"
              style={{ fontFamily: 'EB Garamond, serif' }}
            >
              {t('partnersTitle')}
            </h2>
            <p className="text-xl text-gray-400">{t('partnersSubtitle')}</p>
          </div>
          
          {/* Grid of Partners with Logos */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {deliveryPartners.map((partner, index) => (
              <div
                key={index}
                className="flex flex-col items-center gap-3 p-6 bg-white rounded-xl shadow-xl hover:shadow-2xl hover:scale-110 transition-all duration-300 border-2 border-transparent hover:border-red-500"
              >
                <img 
                  src={`/images/partners/${partner.logo}`}
                  alt={partner.name}
                  className="w-20 h-20 object-contain"
                />
                <span className="text-sm font-bold text-gray-800 text-center">{partner.name}</span>
              </div>
            ))}
          </div>
          
          <p className="text-center text-gray-400 mt-12 text-lg">
            {t('partnersMore')}
          </p>
        </div>
      </section>

      {/* AI & Technology Section */}
      <section className="py-24 bg-gradient-to-b from-gray-900 to-black relative overflow-hidden">
        {/* Animated Background Elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-10 w-72 h-72 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        </div>
        
        <div className="container mx-auto px-4 max-w-7xl relative z-10">
          <div className="text-center mb-16">
            <div className="inline-block mb-4">
              <Brain className="w-20 h-20 text-red-500 animate-pulse" />
            </div>
            <h2 
              className="text-5xl font-bold mb-4 bg-gradient-to-r from-red-400 via-orange-400 to-yellow-400 bg-clip-text text-transparent"
              style={{ fontFamily: 'EB Garamond, serif' }}
            >
              {t('aiTitle')}
            </h2>
            <p className="text-xl text-gray-400">{t('aiSubtitle')}</p>
          </div>
          
          {/* AI Features */}
          <div className="grid md:grid-cols-2 gap-8 mb-16">
            {aiFeatures.map((feature, index) => (
              <div
                key={index}
                className="group p-8 rounded-3xl bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 hover:border-red-500 transition-all duration-500 hover:scale-105"
              >
                <div className={`${feature.color} mb-6 group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className="text-3xl font-bold mb-4 text-white">{t(feature.titleKey)}</h3>
                <p className="text-gray-400 text-lg leading-relaxed">{t(feature.descKey)}</p>
              </div>
            ))}
          </div>
          
          {/* Powered By AI Models */}
          <div className="text-center mt-20">
            <p className="text-gray-500 text-sm uppercase tracking-wider mb-6">{t('poweredBy')}</p>
            <div className="flex justify-center items-center gap-12 flex-wrap">
              {aiModels.map((model, index) => (
                <div
                  key={index}
                  className="group flex flex-col items-center gap-3 hover:scale-110 transition-transform duration-300"
                >
                  <div className="text-5xl group-hover:animate-bounce">{model.icon}</div>
                  <span className="text-gray-400 font-medium group-hover:text-white transition-colors">{model.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-red-600 to-orange-600 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="container mx-auto px-4 text-center relative z-10">
          <h2 className="text-5xl font-bold mb-6 text-white" style={{ fontFamily: 'EB Garamond, serif' }}>
            {t('ctaTitle')}
          </h2>
          <p className="text-2xl text-white/90 mb-10">
            {t('ctaSubtitle')}
          </p>
          <Button
            size="lg"
            onClick={() => navigate('/register')}
            className="bg-white text-red-600 hover:bg-gray-100 text-xl px-12 py-8 rounded-full shadow-2xl transform hover:scale-105 transition-all border-0 font-bold"
          >
            {t('ctaButton')}
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black border-t border-gray-800 py-16">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="grid md:grid-cols-3 gap-12 mb-12">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-2xl">B</span>
                </div>
                <span className="text-2xl font-bold text-white">Beyond Express</span>
              </div>
              <p className="text-gray-400 leading-relaxed">
                La plateforme 3PL la plus avancée d'Algérie. Propulsée par l'Intelligence Artificielle.
              </p>
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-white mb-4">Services</h3>
              <ul className="space-y-3 text-gray-400">
                <li className="hover:text-red-400 transition-colors cursor-pointer">Stockage</li>
                <li className="hover:text-red-400 transition-colors cursor-pointer">Fulfillment</li>
                <li className="hover:text-red-400 transition-colors cursor-pointer">Livraison</li>
                <li className="hover:text-red-400 transition-colors cursor-pointer">Score de Risque IA</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-white mb-4">Contact</h3>
              <ul className="space-y-3 text-gray-400">
                <li className="hover:text-red-400 transition-colors">📧 contact@beyondexpress-batna.com</li>
                <li className="hover:text-red-400 transition-colors">📧 beyondexpress@hotmail.com</li>
                <li className="hover:text-red-400 transition-colors">📞 +213 655 36 33 16</li>
                <li className="hover:text-red-400 transition-colors">📞 +213 784 20 03 41</li>
                <li className="hover:text-red-400 transition-colors">📍 cité 84 Logs Batna, Algeria</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8 text-center text-gray-500">
            <p>&copy; 2025 Beyond Express. Tous droits réservés. Made with ❤️ in Algeria</p>
          </div>
        </div>
      </footer>

      {/* Custom CSS for scroll animation */}
      <style jsx>{`
        @keyframes scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        
        .animate-scroll {
          animation: scroll 30s linear infinite;
        }
        
        .animate-scroll:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
};

export default LandingPageModern;
