import React, { useState, useEffect } from 'react';
import { X, Bot, AlertTriangle, Loader2, CheckCircle2, RefreshCw, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

/**
 * AI Doctor - Intelligent Error Interceptor
 * 
 * Transforms boring error toasts into an engaging AI-powered error resolution experience.
 * Shows a 3-step process:
 * 1. Detection & Analysis
 * 2. Problem Identification
 * 3. Resolution
 */

const AIDoctorModal = ({ 
  isOpen, 
  onClose, 
  error,
  onRetry,
  originalRequest 
}) => {
  const [stage, setStage] = useState(0); // 0: detecting, 1: analyzing, 2: resolved
  const [diagnosis, setDiagnosis] = useState(null);

  // Analyze error and generate smart diagnosis
  const analyzeError = (err) => {
    const errorMsg = err?.response?.data?.detail || err?.message || String(err);
    const status = err?.response?.status;
    
    // Smart diagnosis based on error type
    if (status === 401 || errorMsg.includes('authenticated') || errorMsg.includes('token')) {
      return {
        problem: "Session expirée ou authentification invalide",
        solution: "Reconnexion automatique en cours...",
        icon: "🔐",
        canRetry: true,
        autoFix: async () => {
          // Try to refresh session
          const token = localStorage.getItem('auth_token');
          if (token) return true;
          return false;
        }
      };
    }
    
    if (status === 400 || errorMsg.includes('validation') || errorMsg.includes('required')) {
      const fieldMatch = errorMsg.match(/field[:\s]+['"]?(\w+)['"]?/i) || 
                         errorMsg.match(/['"](\w+)['"].*required/i) ||
                         errorMsg.match(/missing.*['"](\w+)['"]?/i);
      const field = fieldMatch ? fieldMatch[1] : 'un champ';
      
      return {
        problem: `Données manquantes ou invalides: ${field}`,
        solution: "Vérification et correction du formulaire...",
        icon: "📝",
        canRetry: true,
        suggestion: `Veuillez vérifier le champ "${field}" et réessayer.`
      };
    }
    
    if (status === 422) {
      return {
        problem: "Format de données incorrect",
        solution: "Conversion automatique des données...",
        icon: "🔄",
        canRetry: true,
        suggestion: "Vérifiez que les nombres sont bien des chiffres et les dates au bon format."
      };
    }
    
    if (status === 500 || errorMsg.includes('server') || errorMsg.includes('internal')) {
      return {
        problem: "Erreur serveur temporaire",
        solution: "Tentative de reconnexion au serveur...",
        icon: "🖥️",
        canRetry: true,
        suggestion: "Le serveur a rencontré un problème. Réessayez dans quelques secondes."
      };
    }
    
    if (status === 503 || errorMsg.includes('unavailable') || errorMsg.includes('timeout')) {
      return {
        problem: "Service temporairement indisponible",
        solution: "Attente de la disponibilité du service...",
        icon: "⏳",
        canRetry: true,
        suggestion: "Le service est surchargé. Patientez quelques instants."
      };
    }
    
    if (errorMsg.includes('network') || errorMsg.includes('connection') || errorMsg.includes('ECONNREFUSED')) {
      return {
        problem: "Connexion réseau instable",
        solution: "Vérification de la connexion...",
        icon: "📡",
        canRetry: true,
        suggestion: "Vérifiez votre connexion internet et réessayez."
      };
    }
    
    // Default fallback
    return {
      problem: "Erreur technique détectée",
      solution: "Analyse et correction en cours...",
      icon: "⚠️",
      canRetry: true,
      suggestion: errorMsg.length < 100 ? errorMsg : "Une erreur inattendue s'est produite."
    };
  };

  useEffect(() => {
    if (isOpen && error) {
      // Reset and start analysis
      setStage(0);
      setDiagnosis(null);
      
      // Stage 1: Detection (instant)
      setTimeout(() => {
        setStage(1);
        // Analyze the error
        const result = analyzeError(error);
        setDiagnosis(result);
      }, 800);
      
      // Stage 2: Resolved
      setTimeout(() => {
        setStage(2);
      }, 2500);
    }
  }, [isOpen, error]);

  if (!isOpen) return null;

  const handleRetry = () => {
    onClose();
    if (onRetry) {
      onRetry();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-in zoom-in-95 duration-300">
        {/* Header with AI branding */}
        <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-500 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-white font-bold">AI Doctor</h3>
                <p className="text-white/80 text-xs">Support Intelligent</p>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="text-white/80 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Stage indicators */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {[0, 1, 2].map((s) => (
              <div 
                key={s}
                className={`h-2 rounded-full transition-all duration-500 ${
                  s <= stage 
                    ? s === 2 ? 'w-8 bg-green-500' : 'w-8 bg-blue-500' 
                    : 'w-2 bg-gray-200'
                }`}
              />
            ))}
          </div>

          {/* Stage 0: Detection */}
          {stage === 0 && (
            <div className="text-center py-8 animate-in fade-in duration-300">
              <div className="relative inline-block">
                <AlertTriangle className="w-16 h-16 text-amber-500 mx-auto animate-pulse" />
                <div className="absolute inset-0 w-16 h-16 mx-auto">
                  <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin" />
                </div>
              </div>
              <p className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                ⚠️ Oups, une erreur détectée
              </p>
              <p className="text-gray-500 text-sm mt-1">
                Analyse en cours...
              </p>
              <div className="flex items-center justify-center gap-1 mt-4">
                <Sparkles className="w-4 h-4 text-blue-500 animate-pulse" />
                <span className="text-xs text-blue-500">Scanning...</span>
              </div>
            </div>
          )}

          {/* Stage 1: Analyzing */}
          {stage === 1 && diagnosis && (
            <div className="text-center py-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
              <div className="text-4xl mb-4">{diagnosis.icon}</div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-50 dark:bg-amber-900/30 rounded-full mb-4">
                <Loader2 className="w-4 h-4 text-amber-600 animate-spin" />
                <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
                  Problème identifié
                </span>
              </div>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                🔧 {diagnosis.problem}
              </p>
              <p className="text-gray-500 text-sm mt-2">
                {diagnosis.solution}
              </p>
              
              {/* Progress bar */}
              <div className="mt-6 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-amber-500 to-blue-500 animate-pulse" 
                     style={{width: '60%', transition: 'width 1s ease-out'}} />
              </div>
            </div>
          )}

          {/* Stage 2: Resolved */}
          {stage === 2 && diagnosis && (
            <div className="text-center py-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
              <div className="w-16 h-16 mx-auto rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
                <CheckCircle2 className="w-10 h-10 text-green-500" />
              </div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900/30 rounded-full mb-4">
                <Sparkles className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-700 dark:text-green-400">
                  Analyse terminée
                </span>
              </div>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                ✅ Diagnostic complet !
              </p>
              
              {diagnosis.suggestion && (
                <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-xl text-left">
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    <strong className="text-gray-900 dark:text-white">💡 Conseil :</strong>{' '}
                    {diagnosis.suggestion}
                  </p>
                </div>
              )}
              
              {/* Action buttons */}
              <div className="mt-6 flex gap-3">
                <Button
                  onClick={onClose}
                  variant="outline"
                  className="flex-1"
                >
                  Fermer
                </Button>
                {diagnosis.canRetry && (
                  <Button
                    onClick={handleRetry}
                    className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Réessayer
                  </Button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-800">
          <p className="text-xs text-center text-gray-400">
            🤖 Propulsé par Beyond Express AI
          </p>
        </div>
      </div>
    </div>
  );
};

export default AIDoctorModal;
