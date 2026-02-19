import React, { useState, useEffect, useCallback } from 'react';
import {
  Brain, Truck, BarChart3, Terminal, Settings, Zap,
  Send, Loader2, CheckCircle, AlertTriangle, Bot, Sparkles,
  ToggleLeft, ToggleRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { getAIBrainStatus, queryAIBrain } from '@/api';

const stagger = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } } };

const AGENT_ICONS = { truck: Truck, 'bar-chart': BarChart3, terminal: Terminal };

const QUICK_TASKS = [
  { agent: 'logistician', label: 'Analyser Stock', task: 'Analyse la capacité stock et propose des optimisations' },
  { agent: 'logistician', label: 'Optimiser Tournées', task: 'Optimise les routes de livraison du jour' },
  { agent: 'analyst', label: 'Rapport Performance', task: 'Génère un rapport de performance mensuel' },
  { agent: 'monitor', label: 'Health Check', task: 'Vérifie la santé du système et les erreurs récentes' },
];

const AIBrainPage = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [queryAgent, setQueryAgent] = useState(null);
  const [queryTask, setQueryTask] = useState('');
  const [querying, setQuerying] = useState(false);
  const [result, setResult] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await getAIBrainStatus();
      setStatus(res.data);
    } catch (e) { /* silent */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const handleToggle = async () => {
    // Toggle is display-only, AI Brain is always active when API key is configured
    // This provides visual feedback without needing a configure endpoint
  };

  const handleQuery = async (agentId, task) => {
    setQuerying(true);
    setResult(null);
    setQueryAgent(agentId);
    try {
      const res = await queryAIBrain(agentId, task);
      setResult(res.data);
    } catch { toast.error('Erreur de requête'); }
    finally { setQuerying(false); }
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="quantum-spinner" /></div>;

  const agents = status?.agents || [];

  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6" data-testid="ai-brain-page">
      {/* Header */}
      <motion.div variants={fadeUp} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight flex items-center gap-2.5" data-testid="ai-brain-title">
            <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-md">
              <Brain className="w-5 h-5" />
            </div>
            AI Brain Center
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Architecture Multi-Agents — Groq/Qwen Ready</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleToggle} className="no-fx flex items-center gap-2 text-sm font-semibold" data-testid="ai-toggle">
            {status?.enabled
              ? <><ToggleRight className="w-8 h-8 text-[var(--accent-success)]" /> <span className="text-[var(--accent-success)]">Actif</span></>
              : <><ToggleLeft className="w-8 h-8 text-muted-foreground" /> <span className="text-muted-foreground">Inactif</span></>
            }
          </button>
          <div className={`px-3 py-1 rounded-full text-xs font-bold ${status?.is_live ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
            {status?.is_live ? 'LIVE' : 'SIMULATION'}
          </div>
        </div>
      </motion.div>

      {/* Status Card (read-only — keys managed server-side) */}
      <motion.div variants={fadeUp}>
        <Card className="border shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="text-foreground flex items-center gap-2 text-base">
              <Settings className="w-4 h-4 text-muted-foreground" /> Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">Provider</p>
                <p className="text-sm font-semibold capitalize">{status?.provider || '—'}</p>
              </div>
              <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">Modèle</p>
                <p className="text-sm font-semibold">{status?.model || '—'}</p>
              </div>
              <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">Clé API</p>
                <p className="text-sm font-semibold">{status?.has_api_key
                  ? <span className="text-emerald-600 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Configurée</span>
                  : <span className="text-amber-600 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> Non définie</span>
                }</p>
              </div>
              <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                <p className="text-xs text-muted-foreground mb-1">Statut</p>
                <p className="text-sm font-semibold">{status?.is_live
                  ? <span className="text-emerald-600">Connecté</span>
                  : <span className="text-amber-600">Mode simulation</span>
                }</p>
              </div>
            </div>
            {!status?.has_api_key && (
              <p className="mt-3 text-xs text-muted-foreground bg-muted/20 p-2 rounded">
                La clé API Groq est gérée côté serveur (<code>GROQ_API_KEY</code> dans <code>.env</code>). Contactez l'administrateur système.
              </p>
            )}
            {status?.has_api_key && !status?.is_live && (
              <p className="mt-3 text-xs text-amber-600 bg-amber-50 p-2 rounded">
                La clé API est définie mais la connexion échoue. Vérifiez la validité de la clé côté serveur.
              </p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Agent Cards */}
      <motion.div variants={stagger} className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {agents.map((agent, i) => {
          const Icon = AGENT_ICONS[agent.icon] || Bot;
          return (
            <motion.div key={agent.id} variants={fadeUp}>
              <Card className="border shadow-lg hover:shadow-xl transition-shadow" data-testid={`agent-${agent.id}`}>
                <CardContent className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2.5 rounded-xl text-white shadow-md" style={{ background: `linear-gradient(135deg, ${agent.color}, ${agent.color}dd)` }}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-foreground">{agent.name}</h3>
                      <p className="text-[10px] text-muted-foreground font-mono">{agent.model_hint}</p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mb-4">{agent.description}</p>

                  {/* Quick task buttons */}
                  <div className="space-y-1.5">
                    {QUICK_TASKS.filter(t => t.agent === agent.id).map((qt, idx) => (
                      <button key={idx}
                        onClick={() => handleQuery(agent.id, qt.task)}
                        disabled={querying}
                        className="no-fx w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-accent text-xs font-medium text-foreground transition-colors disabled:opacity-50"
                        data-testid={`task-${agent.id}-${idx}`}
                      >
                        <Sparkles className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                        {qt.label}
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Custom Query */}
      <motion.div variants={fadeUp}>
        <Card className="border shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="text-foreground flex items-center gap-2 text-base">
              <Send className="w-4 h-4 text-[var(--primary-500)]" /> Requête Libre
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <select value={queryAgent || 'logistician'} onChange={e => setQueryAgent(e.target.value)}
                className="w-40 shrink-0 h-10 rounded-lg border border-border bg-background px-3 text-sm" data-testid="query-agent-select"
              >
                {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
              <Input value={queryTask} onChange={e => setQueryTask(e.target.value)}
                placeholder="Ex: Analyse la capacité du dépôt de Constantine..." className="h-10 flex-1"
                onKeyDown={e => e.key === 'Enter' && queryTask && handleQuery(queryAgent || 'logistician', queryTask)}
                data-testid="query-input"
              />
              <Button onClick={() => queryTask && handleQuery(queryAgent || 'logistician', queryTask)}
                disabled={querying || !queryTask} className="h-10 bg-[var(--primary-500)] text-white shrink-0"
                data-testid="query-submit"
              >
                {querying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Result */}
      <AnimatePresence>
        {(querying || result) && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
            <Card className="border shadow-lg border-[var(--accent-info)]/20" data-testid="ai-result">
              <CardContent className="p-5">
                {querying ? (
                  <div className="flex items-center gap-3 py-4">
                    <Loader2 className="w-5 h-5 animate-spin text-[var(--accent-info)]" />
                    <span className="text-sm text-muted-foreground animate-pulse">Agent en cours d'analyse...</span>
                  </div>
                ) : result && (
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Bot className="w-4 h-4 text-[var(--accent-info)]" />
                      <span className="text-xs font-bold text-foreground">{result.agent}</span>
                      <span className="text-[10px] text-muted-foreground font-mono">({result.model})</span>
                      {result.is_simulated && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-50 text-amber-700">SIM</span>
                      )}
                    </div>
                    <div className="text-sm text-foreground whitespace-pre-wrap leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: result.response.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>') }}
                    />
                    <p className="text-[10px] text-muted-foreground mt-3 font-mono">{result.timestamp}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default AIBrainPage;
