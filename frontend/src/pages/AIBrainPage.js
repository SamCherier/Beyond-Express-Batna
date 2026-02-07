import React, { useState, useEffect, useCallback } from 'react';
import {
  Brain, Truck, BarChart3, Terminal, Settings, Zap, Key,
  Send, Loader2, CheckCircle, AlertTriangle, Bot, Sparkles,
  ToggleLeft, ToggleRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { getAIBrainStatus, configureAIBrain, queryAIBrain } from '@/api';

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
  const [apiKey, setApiKey] = useState('');
  const [provider, setProvider] = useState('groq');
  const [model, setModel] = useState('llama-3.3-70b-versatile');
  const [saving, setSaving] = useState(false);
  const [queryAgent, setQueryAgent] = useState(null);
  const [queryTask, setQueryTask] = useState('');
  const [querying, setQuerying] = useState(false);
  const [result, setResult] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await getAIBrainStatus();
      setStatus(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      await configureAIBrain({ api_key: apiKey || null, provider, model, enabled: status?.enabled ?? true });
      toast.success('Configuration sauvegardée');
      setApiKey('');
      fetchStatus();
    } catch { toast.error('Erreur de configuration'); }
    finally { setSaving(false); }
  };

  const handleToggle = async () => {
    try {
      await configureAIBrain({ enabled: !(status?.enabled), provider: status?.provider || 'groq', model: status?.model || 'llama-3.3-70b-versatile' });
      fetchStatus();
      toast.success(status?.enabled ? 'AI désactivée' : 'AI activée');
    } catch { toast.error('Erreur'); }
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

      {/* Config Card */}
      <motion.div variants={fadeUp}>
        <Card className="border shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="text-foreground flex items-center gap-2 text-base">
              <Settings className="w-4 h-4 text-muted-foreground" /> Configuration LLM
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div>
                <label className="text-xs text-muted-foreground font-semibold mb-1 block">Clé API (Groq/OpenAI)</label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)}
                    placeholder={status?.has_api_key ? '••••••••' : 'gsk_xxxxx...'} className="pl-9 h-10"
                    data-testid="api-key-input"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-foreground font-semibold mb-1 block">Provider</label>
                <select value={provider} onChange={e => setProvider(e.target.value)}
                  className="w-full h-10 rounded-lg border border-border bg-background px-3 text-sm" data-testid="provider-select"
                >
                  <option value="groq">Groq (Gratuit & Rapide)</option>
                  <option value="openai">OpenAI</option>
                  <option value="custom">Custom Endpoint</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground font-semibold mb-1 block">Modèle</label>
                <select value={model} onChange={e => setModel(e.target.value)}
                  className="w-full h-10 rounded-lg border border-border bg-background px-3 text-sm" data-testid="model-select"
                >
                  <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Recommandé)</option>
                  <option value="llama-3.1-8b-instant">Llama 3.1 8B Instant</option>
                  <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                  <option value="gemma2-9b-it">Gemma 2 9B</option>
                </select>
              </div>
              <div className="flex items-end">
                <Button onClick={handleSaveConfig} disabled={saving} className="w-full h-10 bg-[var(--primary-500)] text-white" data-testid="save-config-btn">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                  Sauvegarder
                </Button>
              </div>
            </div>
            {!status?.is_live && (
              <p className="text-xs text-amber-600 mt-3 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                Mode simulation actif. Entrez une clé API Groq gratuite pour activer les agents réels.
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
