import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import BeyondExpressLogo from '@/components/BeyondExpressLogo';
import { toast } from 'sonner';
import { Mail, Lock, User, Loader2, Briefcase } from 'lucide-react';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { register: registerUser, loginWithGoogle } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'ecommerce'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await registerUser(formData.email, formData.password, formData.name, formData.role);
      toast.success('Compte créé avec succès!');
      navigate('/login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('language', lng);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-red-50 flex items-center justify-center p-4" data-testid="register-page">
      {/* Language Switcher */}
      <div className="fixed top-4 right-4 flex gap-2 z-50">
        <button
          onClick={() => changeLanguage('fr')}
          className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
            i18n.language === 'fr' ? 'bg-red-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100 shadow-sm'
          }`}
        >
          FR
        </button>
        <button
          onClick={() => changeLanguage('ar')}
          className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
            i18n.language === 'ar' ? 'bg-red-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100 shadow-sm'
          }`}
        >
          AR
        </button>
        <button
          onClick={() => changeLanguage('en')}
          className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
            i18n.language === 'en' ? 'bg-red-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-100 shadow-sm'
          }`}
        >
          EN
        </button>
      </div>

      <Card className="w-full max-w-md shadow-2xl border-0">
        <CardHeader className="space-y-4 pb-6">
          <div className="flex justify-center">
            <BeyondExpressLogo size="md" />
          </div>
          <div className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'EB Garamond, serif' }}>
              {t('signUp')}
            </CardTitle>
            <CardDescription className="text-base mt-2">
              Créez votre compte Beyond Express
            </CardDescription>
          </div>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium">
                {t('name')}
              </Label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                <Input
                  id="name"
                  type="text"
                  placeholder="Votre nom complet"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="pl-10 h-11"
                  required
                  data-testid="name-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">
                {t('email')}
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  placeholder="vous@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="pl-10 h-11"
                  required
                  data-testid="email-input"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">
                {t('password')}
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="pl-10 h-11"
                  required
                  minLength={6}
                  data-testid="password-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="role" className="text-sm font-medium">
                {t('role')}
              </Label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-3 h-5 w-5 text-gray-400 z-10" />
                <Select
                  value={formData.role}
                  onValueChange={(value) => setFormData({ ...formData, role: value })}
                >
                  <SelectTrigger className="pl-10 h-11" data-testid="role-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ecommerce" data-testid="role-ecommerce">{t('ecommerce')}</SelectItem>
                    <SelectItem value="admin" data-testid="role-admin">{t('admin')}</SelectItem>
                    <SelectItem value="delivery" data-testid="role-delivery">{t('delivery')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-red-500 hover:bg-red-600 text-white font-medium mt-6"
              disabled={loading}
              data-testid="register-submit-button"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('loading')}
                </>
              ) : (
                t('signUp')
              )}
            </Button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-white px-4 text-gray-500">{t('orContinueWith')}</span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full h-11 border-2 hover:bg-gray-50"
            onClick={loginWithGoogle}
            data-testid="google-register-button"
          >
            <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            {t('googleSignIn')}
          </Button>

          <div className="mt-6 text-center text-sm">
            <span className="text-gray-600">Déjà un compte?</span>{' '}
            <Link to="/login" className="text-red-500 hover:text-red-600 font-medium hover:underline" data-testid="login-link">
              {t('signIn')}
            </Link>
          </div>

          <div className="mt-4 text-center">
            <Link to="/" className="text-sm text-gray-500 hover:text-gray-700 hover:underline">
              ← Retour à l'accueil
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RegisterPage;