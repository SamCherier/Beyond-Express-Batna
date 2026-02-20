import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Package, Truck, MessageCircle, Brain, Zap, Shield, ChevronRight,
  Sparkles, TrendingUp, BarChart3, Globe, Play, ArrowRight, Cpu,
  Route, Bot, Boxes, CheckCircle
} from 'lucide-react';
import './LandingDarkTech.css';

const LOGO_VIDEO = 'https://customer-assets.emergentagent.com/job_89cb861e-faaf-4249-88f9-d33e81a27a6b/artifacts/hp63cg0h_%D8%A5%D9%86%D8%B4%D8%A7%D8%A1_%D9%81%D9%8A%D8%AF%D9%8A%D9%88_%D8%B4%D8%B9%D8%A7%D8%B1_%D8%B3%D9%8A%D9%86%D9%85%D8%A7%D8%A6%D9%8A_%D9%85%D8%A8%D9%87%D8%B1.mp4';
const BG_VIDEO = 'https://customer-assets.emergentagent.com/job_89cb861e-faaf-4249-88f9-d33e81a27a6b/artifacts/th45srtm_Logistics_AI_Platform_Background_Video.mp4';

/* ── Frosted Glass Navbar ── */
const Navbar = ({ navigate, i18n, changeLanguage }) => (
  <nav className="fixed top-0 w-full z-50 glass" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
    <div className="container mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#E61E2A] to-[#ff4d4d] flex items-center justify-center font-bold text-white text-lg" style={{ fontFamily: 'Montserrat' }}>B</div>
        <span className="text-lg font-bold text-white hidden sm:block" style={{ fontFamily: 'Montserrat' }}>Beyond Express</span>
      </div>
      <div className="flex items-center gap-2 sm:gap-3">
        <button onClick={() => navigate('/tracking')} className="hidden md:flex items-center gap-1.5 text-sm text-gray-400 hover:text-[#00F2FF] transition-colors px-3 py-1.5">
          <Package className="w-4 h-4" /> Suivre un Colis
        </button>
        <div className="hidden md:flex gap-1">
          {['fr','ar','en'].map(l => (
            <button key={l} onClick={() => changeLanguage(l)}
              className={`px-2.5 py-1 rounded text-xs font-semibold uppercase transition-all ${
                i18n.language === l ? 'bg-[#00F2FF]/15 text-[#00F2FF] border border-[#00F2FF]/30' : 'text-gray-500 hover:text-gray-300'
              }`}>{l}</button>
          ))}
        </div>
        <button onClick={() => navigate('/login')} className="btn-neon-cyan text-sm font-semibold px-4 py-2 rounded-lg">Connexion</button>
        <button onClick={() => navigate('/register')} className="btn-neon-red text-sm font-semibold px-4 py-2 rounded-lg">Commencer</button>
      </div>
    </div>
  </nav>
);

/* ── Feature Card (Floating 3D Widget) ── */
const FeatureCard = ({ icon: Icon, title, desc, color, delay }) => (
  <div className="float-widget glass-strong rounded-2xl p-6 sm:p-8 group hover:border-[color:var(--cyan)] transition-all duration-500 cursor-default" style={{ animationDelay: `${delay}s` }}>
    <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-5 transition-transform group-hover:scale-110" style={{ background: `linear-gradient(135deg, ${color}30, ${color}10)`, border: `1px solid ${color}40` }}>
      <Icon className="w-6 h-6" style={{ color }} />
    </div>
    <h3 className="text-lg font-bold text-white mb-2" style={{ fontFamily: 'Montserrat' }}>{title}</h3>
    <p className="text-sm text-gray-400 leading-relaxed">{desc}</p>
    <div className="mt-5 flex items-center gap-1 text-xs font-semibold transition-all group-hover:gap-2" style={{ color }}>
      Explorer <ChevronRight className="w-3.5 h-3.5" />
    </div>
  </div>
);

/* ── Stat Widget ── */
const StatWidget = ({ value, label, glowClass }) => (
  <div className="glass rounded-2xl p-6 sm:p-8 text-center">
    <div className={`text-4xl sm:text-5xl font-black mb-2 ${glowClass}`} style={{ fontFamily: 'Montserrat' }}>{value}</div>
    <p className="text-sm text-gray-500 font-medium">{label}</p>
  </div>
);

/* ═══════════ MAIN COMPONENT ═══════════ */
const LandingPageModernV2 = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const changeLanguage = (lng) => i18n.changeLanguage(lng);
  const [logoReady, setLogoReady] = useState(false);

  const features = [
    { icon: Brain, title: 'AI Reconciliation', desc: 'Réconciliation financière automatisée. Fini les erreurs de comptabilité et les litiges COD.', color: '#00F2FF', delay: 0 },
    { icon: Route, title: 'Smart Routing', desc: 'Optimisation intelligente des routes de livraison pour réduire les coûts et les délais.', color: '#8B5CF6', delay: -2 },
    { icon: Bot, title: 'WhatsApp Bot', desc: 'Support client Darja/FR/AR automatique 24/7. Réponses instantanées à vos clients.', color: '#10B981', delay: -4 },
    { icon: Shield, title: 'Audit Immutable', desc: 'Chaîne de hash cryptographique pour chaque action. Traçabilité totale conforme ISO.', color: '#E61E2A', delay: -1 },
    { icon: Boxes, title: 'Multi-Entrepôt', desc: 'Gestion visuelle de vos zones de stockage en temps réel avec alertes de capacité.', color: '#F59E0B', delay: -3 },
    { icon: Cpu, title: 'AI Brain Center', desc: '3 agents IA spécialisés alimentés par Llama 3.3 Open Source — analyses ultra-rapides et gratuites.', color: '#00F2FF', delay: -5 },
  ];

  const partners = [
    { name: 'Yalidine', emoji: '🚚' },
    { name: 'ZR Express', emoji: '📦' },
    { name: 'Procolis', emoji: '🎯' },
    { name: 'Maystro', emoji: '⚡' },
    { name: 'DHD', emoji: '🛵' },
  ];

  return (
    <div className="dark-tech min-h-screen">
      <Navbar navigate={navigate} i18n={i18n} changeLanguage={changeLanguage} />

      {/* ════════ HERO ════════ */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Scanline */}
        <div className="scanline-overlay" />

        {/* Grid BG */}
        <div className="absolute inset-0 grid-bg z-[1]" />

        {/* Radial glow behind logo */}
        <div className="absolute inset-0 z-[1]" style={{ background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(0,242,255,0.06) 0%, transparent 70%)' }} />

        {/* Content */}
        <div className="relative z-10 container mx-auto px-4 sm:px-6 text-center pt-24 pb-16 sm:pt-28">
          {/* Logo Video with Pulse */}
          <div className="flex justify-center mb-8 sm:mb-10">
            <div className="logo-pulse-wrap w-40 h-40 sm:w-56 sm:h-56 lg:w-64 lg:h-64">
              <video
                className="logo-video"
                src={LOGO_VIDEO}
                autoPlay loop muted playsInline
                onCanPlay={() => setLogoReady(true)}
              />
            </div>
          </div>

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs sm:text-sm font-semibold mb-6" style={{ color: '#00F2FF', borderColor: 'rgba(0,242,255,0.2)' }}>
            <Sparkles className="w-3.5 h-3.5" /> Powered by Llama 3.3 70B — Open Source &amp; Gratuit
          </div>

          {/* Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-black leading-[1.1] mb-4" style={{ fontFamily: 'Montserrat' }}>
            <span className="text-white">La Logistique</span><br />
            <span className="text-gradient-cyan">Intelligente</span>
          </h1>

          {/* Darja tagline */}
          <p className="text-lg sm:text-xl text-gray-400 mb-3 max-w-2xl mx-auto" style={{ fontFamily: 'Hacen Tunisia, serif', lineHeight: '1.8' }}>
            خليك مركز على البيع، احنا نديرولك التوصيل
          </p>
          <p className="text-sm sm:text-base text-gray-500 mb-10 max-w-xl mx-auto">
            Première plateforme algérienne de logistique automatisée par IA. 58 wilayas couvertes.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            <button onClick={() => navigate('/register')} className="btn-neon-red text-base font-bold px-8 py-3.5 rounded-xl flex items-center gap-2 group">
              Commencer Gratuitement <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <button onClick={() => navigate('/tracking')} className="btn-neon-cyan text-base font-bold px-8 py-3.5 rounded-xl flex items-center gap-2">
              <Package className="w-4 h-4" /> Suivre un Colis
            </button>
          </div>
        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#050505] to-transparent z-10" />
      </section>

      {/* ════════ AI FEATURES ════════ */}
      <section className="relative py-20 sm:py-28 px-4 sm:px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-semibold mb-4" style={{ color: '#00F2FF' }}>
              <Brain className="w-3.5 h-3.5" /> Intelligence Artificielle
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white mb-3" style={{ fontFamily: 'Montserrat' }}>
              Automatisez <span className="text-gradient-cyan">Tout</span>
            </h2>
            <p className="text-base text-gray-500 max-w-lg mx-auto">6 modules IA qui travaillent pour vous 24/7</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f, i) => <FeatureCard key={i} {...f} />)}
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* ════════ VIDEO SHOWCASE ════════ */}
      <section className="relative py-20 sm:py-28 px-4 sm:px-6 overflow-hidden">
        {/* Subtle grid */}
        <div className="absolute inset-0 grid-bg" />

        <div className="container mx-auto max-w-5xl relative z-10">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-black text-white mb-3" style={{ fontFamily: 'Montserrat' }}>
              Plateforme <span className="text-gradient-red">Next-Gen</span>
            </h2>
            <p className="text-base text-gray-500">Visualisez l'avenir de la logistique algérienne</p>
          </div>

          {/* 3D Bezel-less Device Frame */}
          <div className="device-frame flex justify-center">
            <div className="device-inner w-full max-w-4xl">
              <video
                src={BG_VIDEO}
                autoPlay loop muted playsInline
                className="w-full"
                style={{ aspectRatio: '16/9' }}
              />
              <div className="device-bezel" />
            </div>
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* ════════ STATS ════════ */}
      <section className="py-20 sm:py-24 px-4 sm:px-6">
        <div className="container mx-auto max-w-5xl">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <StatWidget value="10,000+" label="Commandes Traitées" glowClass="text-gradient-cyan stat-glow-cyan" />
            <StatWidget value="500+" label="Marchands Actifs" glowClass="text-gradient-red stat-glow-red" />
            <StatWidget value="99.2%" label="Taux de Livraison" glowClass="text-gradient-cyan stat-glow-cyan" />
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* ════════ PRICING PACKS ════════ */}
      <section className="relative py-20 sm:py-28 px-4 sm:px-6" data-testid="pricing-section">
        <div className="absolute inset-0 z-0" style={{ background: 'radial-gradient(ellipse 70% 50% at 50% 30%, rgba(0,242,255,0.04) 0%, transparent 70%)' }} />
        <div className="container mx-auto max-w-6xl relative z-10">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-semibold mb-4" style={{ color: '#00F2FF' }}>
              <Zap className="w-3.5 h-3.5" /> Offres &amp; Tarifs
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white mb-3" style={{ fontFamily: 'Montserrat' }}>
              Choisissez Votre <span className="text-gradient-cyan">Pack</span>
            </h2>
            <p className="text-base text-gray-500 max-w-lg mx-auto">Des tarifs transparents. Pas de frais cachés. Évoluez sans limite.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* STARTER */}
            <div className="glass-strong rounded-2xl p-8 group hover:border-[#00F2FF]/30 transition-all duration-500 relative overflow-hidden" data-testid="pack-starter">
              <div className="absolute top-0 left-0 w-full h-[2px]" style={{ background: 'linear-gradient(90deg, transparent, rgba(0,242,255,0.3), transparent)' }} />
              <p className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Starter</p>
              <div className="flex items-end gap-1 mb-1">
                <span className="text-4xl font-black text-white" style={{ fontFamily: 'Montserrat' }}>0</span>
                <span className="text-lg font-bold text-gray-400 mb-1">DA</span>
              </div>
              <p className="text-xs text-gray-500 mb-6">Gratuit pour toujours</p>
              <ul className="space-y-3 mb-8">
                {['50 commandes/mois', '1 entrepôt', 'Suivi en temps réel', 'AI Brain (Simulation)', 'Support email'].map((f, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-sm text-gray-400">
                    <CheckCircle className="w-4 h-4 text-[#00F2FF]/60 shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              <button onClick={() => navigate('/register')} className="w-full btn-neon-cyan text-sm font-bold py-3 rounded-xl">
                Commencer
              </button>
            </div>

            {/* PRO — Popular */}
            <div className="relative rounded-2xl p-8 group transition-all duration-500 overflow-hidden" data-testid="pack-pro"
              style={{ background: 'linear-gradient(135deg, rgba(0,242,255,0.08), rgba(139,92,246,0.06))', border: '1.5px solid rgba(0,242,255,0.25)' }}>
              <div className="absolute top-0 left-0 w-full h-[2px]" style={{ background: 'linear-gradient(90deg, #00F2FF, #8B5CF6)' }} />
              <div className="absolute -top-0 right-4 px-3 py-1 rounded-b-lg text-[10px] font-black uppercase tracking-wider" style={{ background: 'linear-gradient(135deg, #00F2FF, #8B5CF6)', color: '#050505' }}>
                Populaire
              </div>
              <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: '#00F2FF' }}>Pro</p>
              <div className="flex items-end gap-1 mb-1">
                <span className="text-4xl font-black text-white" style={{ fontFamily: 'Montserrat' }}>4,900</span>
                <span className="text-lg font-bold text-gray-400 mb-1">DA/mois</span>
              </div>
              <p className="text-xs text-gray-500 mb-6">Pour les marchands en croissance</p>
              <ul className="space-y-3 mb-8">
                {['500 commandes/mois', '3 entrepôts', 'AI Brain LIVE (Llama 3.3)', 'WhatsApp automatique', 'Multi-transporteurs', 'Rapports avancés'].map((f, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-sm text-gray-300">
                    <CheckCircle className="w-4 h-4 text-[#00F2FF] shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              <button onClick={() => navigate('/register')} className="w-full btn-neon-red text-sm font-bold py-3 rounded-xl">
                Essai Gratuit 14 jours
              </button>
            </div>

            {/* BUSINESS */}
            <div className="glass-strong rounded-2xl p-8 group hover:border-[#E61E2A]/30 transition-all duration-500 relative overflow-hidden" data-testid="pack-business">
              <div className="absolute top-0 left-0 w-full h-[2px]" style={{ background: 'linear-gradient(90deg, transparent, rgba(230,30,42,0.4), transparent)' }} />
              <p className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Business</p>
              <div className="flex items-end gap-1 mb-1">
                <span className="text-4xl font-black text-white" style={{ fontFamily: 'Montserrat' }}>Sur Mesure</span>
              </div>
              <p className="text-xs text-gray-500 mb-6">Solutions entreprise</p>
              <ul className="space-y-3 mb-8">
                {['Commandes illimitées', 'Entrepôts illimités', 'API dédiée', 'Account Manager', 'SLA garanti 99.9%', 'Intégration sur-mesure'].map((f, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-sm text-gray-400">
                    <CheckCircle className="w-4 h-4 text-[#E61E2A]/60 shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              <button onClick={() => navigate('/register')} className="w-full btn-neon-cyan text-sm font-bold py-3 rounded-xl">
                Nous Contacter
              </button>
            </div>
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* ════════ PARTNERS (Premium Glassmorphism) ════════ */}
      <section className="relative py-20 sm:py-24 px-4 sm:px-6" data-testid="partners-section">
        <div className="absolute inset-0 z-0" style={{ background: 'radial-gradient(ellipse 60% 40% at 50% 50%, rgba(139,92,246,0.04) 0%, transparent 70%)' }} />
        <div className="container mx-auto max-w-5xl relative z-10">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-xs font-semibold mb-4" style={{ color: '#8B5CF6' }}>
              <Globe className="w-3.5 h-3.5" /> Réseau de Transporteurs
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-white mb-3" style={{ fontFamily: 'Montserrat' }}>
              Nos <span style={{ background: 'linear-gradient(135deg, #8B5CF6, #00F2FF)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Partenaires</span>
            </h2>
            <p className="text-base text-gray-500">Intégration directe avec les leaders du transport algérien</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {[
              { name: 'Yalidine', color: '#E61E2A', icon: Truck, desc: 'Leader national' },
              { name: 'ZR Express', color: '#3B82F6', icon: Package, desc: 'Express 24h' },
              { name: 'Procolis', color: '#10B981', icon: Zap, desc: 'E-commerce' },
              { name: 'Maystro', color: '#F59E0B', icon: TrendingUp, desc: 'Smart delivery' },
              { name: 'DHD', color: '#8B5CF6', icon: Globe, desc: 'Dernière mile' },
            ].map((p, i) => (
              <div key={i} className="glass-strong rounded-2xl p-5 text-center group hover:scale-105 transition-all duration-300 cursor-default"
                style={{ '--glow': p.color }}
                onMouseEnter={e => e.currentTarget.style.boxShadow = `0 0 30px ${p.color}20, inset 0 0 20px ${p.color}08`}
                onMouseLeave={e => e.currentTarget.style.boxShadow = 'none'}
              >
                <div className="w-12 h-12 rounded-xl mx-auto mb-3 flex items-center justify-center transition-transform group-hover:scale-110"
                  style={{ background: `linear-gradient(135deg, ${p.color}25, ${p.color}08)`, border: `1px solid ${p.color}30` }}>
                  <p.icon className="w-5 h-5" style={{ color: p.color }} />
                </div>
                <p className="text-sm font-bold text-white mb-0.5" style={{ fontFamily: 'Montserrat' }}>{p.name}</p>
                <p className="text-[10px] text-gray-500">{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* ════════ CTA ════════ */}
      <section className="relative py-24 sm:py-32 px-4 sm:px-6 overflow-hidden">
        <div className="absolute inset-0 z-0" style={{ background: 'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(230,30,42,0.1) 0%, transparent 60%)' }} />
        <div className="container mx-auto max-w-3xl text-center relative z-10">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white mb-5" style={{ fontFamily: 'Montserrat' }}>
            Prêt à <span className="text-gradient-red">Transformer</span> Votre Business ?
          </h2>
          <p className="text-base text-gray-400 mb-10 max-w-xl mx-auto">
            Rejoignez des centaines de marchands qui ont automatisé leur logistique avec Beyond Express.
          </p>
          <button onClick={() => navigate('/register')} className="btn-neon-red text-lg font-bold px-10 py-4 rounded-xl inline-flex items-center gap-2 group">
            Démarrer Gratuitement <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
          </button>
        </div>
      </section>

      {/* ════════ FOOTER ════════ */}
      <footer className="border-t border-white/5 py-10 px-4 sm:px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#E61E2A] to-[#ff4d4d] flex items-center justify-center font-bold text-white text-sm" style={{ fontFamily: 'Montserrat' }}>B</div>
              <span className="font-bold text-white text-sm" style={{ fontFamily: 'Montserrat' }}>Beyond Express</span>
            </div>
            <div className="flex gap-6 text-xs text-gray-600">
              <button onClick={() => navigate('/tracking')} className="hover:text-[#00F2FF] transition-colors">Suivre un Colis</button>
              <button onClick={() => navigate('/login')} className="hover:text-[#00F2FF] transition-colors">Se Connecter</button>
              <button onClick={() => navigate('/register')} className="hover:text-[#00F2FF] transition-colors">S'inscrire</button>
            </div>
          </div>
          <div className="mt-8 pt-6 border-t border-white/5 text-center text-xs text-gray-700">
            © 2025 Beyond Express — Plateforme de Livraison Algérienne
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPageModernV2;
