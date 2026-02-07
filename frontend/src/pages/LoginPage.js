import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import BeyondExpressLogo from '@/components/BeyondExpressLogo';
import { toast } from 'sonner';
import { Mail, Lock, Loader2, Zap, Truck, Star, Shield, ChevronLeft, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const TESTIMONIALS = [
  { quote: "Meilleure plateforme logistique que nous ayons utilisée !", author: "Sarah M.", role: "Manager E-commerce", rating: 5 },
  { quote: "Nos délais de livraison ont chuté de 40%", author: "Mohammed A.", role: "Directeur Opérations", rating: 5 },
  { quote: "La satisfaction client est au maximum !", author: "Fatima K.", role: "Responsable Service Client", rating: 5 },
];

const FEATURES = [
  { icon: Zap, text: "Suivi en temps réel" },
  { icon: Truck, text: "Optimisation intelligente des tournées" },
  { icon: Star, text: "Satisfaction client garantie" },
];

const STATS = [
  { number: "50K+", label: "Livraisons/jour" },
  { number: "99.8%", label: "Taux ponctualité" },
  { number: "4.9", label: "Note clients" },
];

const LoginPage = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { login, loginWithGoogle } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [testimonialIdx, setTestimonialIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setTestimonialIdx(i => (i + 1) % TESTIMONIALS.length), 5000);
    return () => clearInterval(timer);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(formData.email, formData.password);
      toast.success('Connexion réussie');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Identifiants incorrects');
    } finally {
      setLoading(false);
    }
  };

  const changeLanguage = (lng) => { i18n.changeLanguage(lng); localStorage.setItem('language', lng); };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* ═══ LEFT: Branding ═══ */}
      <div className="hidden lg:flex lg:w-[52%] relative bg-[var(--primary-900)] overflow-hidden">
        {/* Animated gradient background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-br from-[var(--primary-900)] via-[#0f3460] to-[#1a1a2e]" />
          <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-[var(--primary-500)] opacity-[0.08] blur-[100px]" />
          <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-[var(--accent-info)] opacity-[0.06] blur-[80px]" />
        </div>

        <div className="relative z-10 flex flex-col justify-between p-10 xl:p-16 w-full">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <BeyondExpressLogo size="sm" />
            <span className="text-white font-bold text-lg tracking-tight">Beyond Express</span>
          </div>

          {/* Hero */}
          <div className="flex-1 flex flex-col justify-center max-w-lg">
            {/* 3D CSS Logo */}
            <div className="mb-8" style={{ perspective: '800px' }}>
              <motion.div
                animate={{ rotateY: [0, 10, -10, 0] }}
                transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
                className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[var(--primary-500)] to-[var(--accent-info)] shadow-2xl shadow-blue-500/30 flex items-center justify-center"
                style={{ transformStyle: 'preserve-3d' }}
              >
                <Truck className="w-10 h-10 text-white" />
              </motion.div>
            </div>

            <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
              className="text-3xl xl:text-4xl font-bold text-white leading-tight mb-4"
            >
              Livrez le bonheur,<br />plus rapidement.
            </motion.h1>

            <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
              className="text-blue-200/80 text-base mb-8"
            >
              La plateforme tout-en-un pour la logistique moderne
            </motion.p>

            {/* Features */}
            <div className="space-y-3 mb-10">
              {FEATURES.map((f, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + i * 0.1 }}
                  className="flex items-center gap-3"
                >
                  <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                    <f.icon className="w-4 h-4 text-blue-300" />
                  </div>
                  <span className="text-sm text-blue-100/90 font-medium">{f.text}</span>
                </motion.div>
              ))}
            </div>

            {/* Testimonial */}
            <div className="relative h-[90px]">
              <AnimatePresence mode="wait">
                <motion.div key={testimonialIdx}
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="absolute inset-0"
                >
                  <p className="text-blue-100/70 text-sm italic mb-2">"{TESTIMONIALS[testimonialIdx].quote}"</p>
                  <div className="flex items-center gap-2">
                    <div className="flex">
                      {[...Array(TESTIMONIALS[testimonialIdx].rating)].map((_, i) => (
                        <Star key={i} className="w-3 h-3 text-amber-400 fill-amber-400" />
                      ))}
                    </div>
                    <span className="text-xs text-blue-200/60">&mdash; {TESTIMONIALS[testimonialIdx].author}, {TESTIMONIALS[testimonialIdx].role}</span>
                  </div>
                </motion.div>
              </AnimatePresence>
              <div className="absolute bottom-0 flex gap-1.5">
                {TESTIMONIALS.map((_, i) => (
                  <button key={i} onClick={() => setTestimonialIdx(i)}
                    className={`no-fx w-1.5 h-1.5 rounded-full transition-all ${i === testimonialIdx ? 'bg-white w-4' : 'bg-white/30'}`}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Stats bar */}
          <div className="flex gap-8">
            {STATS.map((s, i) => (
              <div key={i}>
                <p className="text-2xl font-bold text-white">{s.number}</p>
                <p className="text-xs text-blue-200/50">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ═══ RIGHT: Form ═══ */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-10 bg-background relative">
        {/* Language switcher */}
        <div className="absolute top-4 right-4 flex gap-1.5">
          {['fr', 'ar', 'en'].map(lng => (
            <button key={lng} onClick={() => changeLanguage(lng)}
              className={`no-fx px-2.5 py-1 rounded-md text-xs font-bold transition-colors
                ${i18n.language === lng ? 'bg-[var(--primary-500)] text-white' : 'text-muted-foreground hover:bg-accent'}`}
            >{lng.toUpperCase()}</button>
          ))}
        </div>

        <div className="w-full max-w-[380px]">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <BeyondExpressLogo size="sm" />
            <span className="text-lg font-bold text-foreground tracking-tight">Beyond Express</span>
          </div>

          <h2 className="text-2xl font-bold text-foreground mb-1" data-testid="login-title">Bon retour</h2>
          <p className="text-sm text-muted-foreground mb-8">Connectez-vous à votre tableau de bord</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-muted-foreground mb-1.5 block">Adresse email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input type="email" placeholder="vous@entreprise.com" value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="pl-10 h-11" required autoFocus data-testid="email-input"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground mb-1.5 block">Mot de passe</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input type={showPassword ? 'text' : 'password'} placeholder="••••••••" value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-10 pr-16 h-11" required data-testid="password-input"
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="no-fx absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground hover:text-foreground font-medium"
                >{showPassword ? 'Masquer' : 'Afficher'}</button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
                <input type="checkbox" className="rounded border-border" /> Se souvenir de moi
              </label>
              <Link to="/forgot-password" className="text-xs text-[var(--primary-500)] hover:underline font-medium">
                Mot de passe oublié ?
              </Link>
            </div>

            <Button type="submit" disabled={loading} data-testid="login-submit-button"
              className="w-full h-11 bg-[var(--primary-500)] hover:bg-[var(--primary-500)]/90 text-white font-semibold shadow-md shadow-blue-500/20"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {loading ? 'Connexion...' : 'Se connecter'}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border" /></div>
            <div className="relative flex justify-center"><span className="bg-background px-3 text-xs text-muted-foreground">ou</span></div>
          </div>

          {/* Google */}
          <Button type="button" variant="outline" className="w-full h-11 border-border font-medium text-sm"
            onClick={loginWithGoogle} data-testid="google-login-button"
          >
            <svg className="mr-2 w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continuer avec Google
          </Button>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            Pas de compte ?{' '}
            <Link to="/register" className="text-[var(--primary-500)] font-semibold hover:underline" data-testid="register-link">
              Créer un compte
            </Link>
          </p>

          {/* Security badge */}
          <div className="mt-8 flex items-center justify-center gap-2 text-[10px] text-muted-foreground">
            <Shield className="w-3.5 h-3.5" />
            <span>Chiffrement SSL 256 bits &mdash; Vos données sont protégées</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
