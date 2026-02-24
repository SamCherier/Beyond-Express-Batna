import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Brain, Key, CheckCircle, XCircle, Loader2, Truck, BarChart3, Shield, Zap, ExternalLink, Save } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/api';

const AGENTS = [
  { id: 'logistician', name: 'Le Logisticien', icon: Truck, color: '#3B82F6', desc: 'Routage, packaging, capacité entrepôt' },
  { id: 'analyst', name: "L'Analyste", icon: BarChart3, color: '#8B5CF6', desc: 'Factures, données, tendances' },
  { id: 'monitor', name: 'Le Moniteur', icon: Shield, color: '#10B981', desc: 'Sécurité, logs, santé système' },
];

const HELP_LINKS = {
  openrouter: 'https://openrouter.ai/keys',
  groq: 'https://console.groq.com/keys',
  together: 'https://api.together.xyz/settings/api-keys',
  moonshot: 'https://platform.moonshot.cn/console/api-keys',
};

const ProviderCard = ({ provider, onKeySaved }) => {
  const [keyInput, setKeyInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const handleSave = async () => {
    if (!keyInput.trim()) return;
    setSaving(true);
    try {
      await api.post('/ai-config/providers/save-key', { provider: provider.id, api_key: keyInput.trim() });
      toast.success(`Clé ${provider.name} sauvegardée`);
      setKeyInput('');
      onKeySaved();
    } catch {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.post('/ai-config/providers/test', { provider: provider.id });
      setTestResult(res.data);
      if (res.data.success) {
        toast.success(`${provider.name} connecté !`);
        onKeySaved();
      }
    } catch {
      setTestResult({ success: false, error: 'Erreur de connexion' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card className="border-border/60" data-testid={`provider-card-${provider.id}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-500" />
            {provider.name}
          </CardTitle>
          <div className="flex items-center gap-1.5">
            {provider.has_key ? (
              <span className="flex items-center gap-1 text-xs font-medium text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30 px-2 py-0.5 rounded-full">
                <CheckCircle className="w-3 h-3" /> Connecté
              </span>
            ) : (
              <span className="text-xs text-muted-foreground bg-muted/40 px-2 py-0.5 rounded-full">Non configuré</span>
            )}
          </div>
        </div>
        <CardDescription className="text-xs">
          {provider.models.length} modèles disponibles
          {provider.key_masked && <span className="ml-2 font-mono text-[10px]">({provider.key_masked})</span>}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input
            type="password"
            placeholder={`Clé API ${provider.name}...`}
            value={keyInput}
            onChange={e => setKeyInput(e.target.value)}
            className="text-xs font-mono h-8"
            data-testid={`key-input-${provider.id}`}
          />
          <Button size="sm" onClick={handleSave} disabled={saving || !keyInput.trim()} className="h-8 px-3" data-testid={`save-key-${provider.id}`}>
            {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={handleTest} disabled={testing || !provider.has_key} className="h-7 text-xs" data-testid={`test-provider-${provider.id}`}>
            {testing ? <><Loader2 className="w-3 h-3 mr-1 animate-spin" /> Test...</> : 'Tester la connexion'}
          </Button>
          <a href={HELP_LINKS[provider.id]} target="_blank" rel="noopener noreferrer" className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1">
            <ExternalLink className="w-3 h-3" /> Obtenir une clé
          </a>
        </div>
        {testResult && (
          <div className={`text-xs p-2 rounded border ${testResult.success ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400' : 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400'}`}>
            {testResult.success ? (
              <><CheckCircle className="w-3 h-3 inline mr-1" />{testResult.response?.substring(0, 100) || 'Connexion réussie'}</>
            ) : (
              <><XCircle className="w-3 h-3 inline mr-1" />{testResult.error}</>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const AgentRow = ({ agent, matrix, providers, onUpdate }) => {
  const agentConfig = matrix[agent.id] || { provider: 'openrouter', model: '' };
  const Icon = agent.icon;

  const availableModels = providers.find(p => p.id === agentConfig.provider)?.models || [];

  const handleProviderChange = (newProvider) => {
    const firstModel = providers.find(p => p.id === newProvider)?.models?.[0]?.id || '';
    onUpdate(agent.id, newProvider, firstModel);
  };

  const handleModelChange = (newModel) => {
    onUpdate(agent.id, agentConfig.provider, newModel);
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 p-3 rounded-lg border border-border/50 bg-card/50" data-testid={`agent-row-${agent.id}`}>
      <div className="flex items-center gap-2 min-w-[160px]">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${agent.color}18`, border: `1px solid ${agent.color}30` }}>
          <Icon className="w-4 h-4" style={{ color: agent.color }} />
        </div>
        <div>
          <p className="text-sm font-bold">{agent.name}</p>
          <p className="text-[10px] text-muted-foreground">{agent.desc}</p>
        </div>
      </div>
      <div className="flex flex-1 gap-2 w-full sm:w-auto">
        <Select value={agentConfig.provider} onValueChange={handleProviderChange}>
          <SelectTrigger className="h-8 text-xs w-[150px]" data-testid={`agent-provider-${agent.id}`}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {providers.filter(p => p.has_key).map(p => (
              <SelectItem key={p.id} value={p.id}><span className="text-xs">{p.name}</span></SelectItem>
            ))}
            {providers.filter(p => !p.has_key).map(p => (
              <SelectItem key={p.id} value={p.id} disabled><span className="text-xs text-muted-foreground">{p.name} (pas de clé)</span></SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={agentConfig.model} onValueChange={handleModelChange}>
          <SelectTrigger className="h-8 text-xs flex-1" data-testid={`agent-model-${agent.id}`}>
            <SelectValue placeholder="Modèle..." />
          </SelectTrigger>
          <SelectContent>
            {availableModels.map(m => (
              <SelectItem key={m.id} value={m.id}><span className="text-xs">{m.label}</span></SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
};

const AIConfigPage = () => {
  const [providers, setProviders] = useState([]);
  const [matrix, setMatrix] = useState({});
  const [loading, setLoading] = useState(true);
  const [savingMatrix, setSavingMatrix] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [pRes, mRes] = await Promise.all([
        api.get('/ai-config/providers'),
        api.get('/ai-config/agent-matrix'),
      ]);
      setProviders(pRes.data);
      setMatrix(mRes.data);
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleAgentUpdate = async (agentId, provider, model) => {
    setMatrix(prev => ({ ...prev, [agentId]: { provider, model } }));
    setSavingMatrix(true);
    try {
      await api.post('/ai-config/agent-matrix', { agent_id: agentId, provider, model });
    } catch {
      toast.error('Erreur de sauvegarde');
    } finally {
      setSavingMatrix(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
    </div>
  );

  return (
    <div className="space-y-6 max-w-5xl mx-auto" data-testid="ai-config-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Brain className="w-6 h-6 text-violet-500" />
          Configuration IA Multi-Agents
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configurez vos fournisseurs d'IA et assignez des modèles à chaque agent spécialisé
        </p>
      </div>

      {/* Provider Keys */}
      <div>
        <h2 className="text-base font-bold mb-3 flex items-center gap-2">
          <Key className="w-4 h-4 text-amber-500" /> Fournisseurs &amp; Clés API
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {providers.map(p => (
            <ProviderCard key={p.id} provider={p} onKeySaved={fetchAll} />
          ))}
        </div>
      </div>

      {/* Agent Matrix */}
      <Card data-testid="agent-matrix-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <Brain className="w-4 h-4 text-violet-500" />
            Matrice d'Agents
            {savingMatrix && <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" />}
          </CardTitle>
          <CardDescription className="text-xs">
            Assignez un fournisseur et un modèle à chaque agent IA spécialisé
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {AGENTS.map(a => (
            <AgentRow key={a.id} agent={a} matrix={matrix} providers={providers} onUpdate={handleAgentUpdate} />
          ))}
        </CardContent>
      </Card>

      {/* Info */}
      <Card className="bg-gradient-to-br from-violet-50 to-blue-50 dark:from-violet-950/20 dark:to-blue-950/20 border-violet-200 dark:border-violet-800">
        <CardContent className="pt-5">
          <h3 className="font-semibold text-violet-900 dark:text-violet-300 text-sm mb-2">Architecture Multi-Providers</h3>
          <ul className="space-y-1.5 text-xs text-violet-800 dark:text-violet-400">
            <li className="flex items-start gap-1.5"><span className="text-violet-500 mt-0.5">-</span><span><strong>OpenRouter</strong> — Accès gratuit aux modèles Llama 3.3, Qwen 3, DeepSeek R1</span></li>
            <li className="flex items-start gap-1.5"><span className="text-violet-500 mt-0.5">-</span><span><strong>Groq</strong> — Inférence ultra-rapide (LPU), Llama &amp; Mixtral</span></li>
            <li className="flex items-start gap-1.5"><span className="text-violet-500 mt-0.5">-</span><span><strong>Together AI</strong> — Open-source haute performance, Qwen 2.5</span></li>
            <li className="flex items-start gap-1.5"><span className="text-violet-500 mt-0.5">-</span><span><strong>Moonshot / Kimi</strong> — Spécialisé en analyse de documents</span></li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIConfigPage;
