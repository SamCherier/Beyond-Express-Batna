import React, { useState, useEffect, useCallback } from 'react';
import {
  MessageCircle, Send, Settings, CheckCircle, AlertTriangle,
  Smartphone, Key, Zap, ExternalLink, Loader2, Phone,
  Bell, ToggleLeft, ToggleRight, RefreshCw, Info, Copy, Check
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import {
  getWhatsAppStatus, configureWhatsApp, sendWhatsAppTest,
  getWhatsAppTemplates, getWhatsAppLogs
} from '@/api';

const fadeUp = { hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0, transition: { duration: 0.3 } } };

/* ── Status Badge ── */
const StatusBadge = ({ configured, enabled }) => {
  if (!configured) return <span className="px-3 py-1 rounded-full text-xs font-bold bg-yellow-500/10 text-yellow-500 border border-yellow-500/20">NON CONFIGURÉ</span>;
  if (!enabled) return <span className="px-3 py-1 rounded-full text-xs font-bold bg-gray-500/10 text-gray-400 border border-gray-500/20">DÉSACTIVÉ</span>;
  return <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">CONNECTÉ</span>;
};

/* ── Template Card ── */
const TemplateCard = ({ tpl }) => (
  <div className="p-4 rounded-xl border border-border/50 bg-card/50 hover:border-emerald-500/30 transition-colors">
    <div className="flex items-center gap-2 mb-2">
      <MessageCircle className="w-4 h-4 text-emerald-500" />
      <span className="font-semibold text-sm">{tpl.label}</span>
      <span className="ml-auto text-[10px] font-mono text-muted-foreground bg-muted/50 px-2 py-0.5 rounded">{tpl.name}</span>
    </div>
    <p className="text-xs text-muted-foreground">{tpl.description}</p>
    {tpl.body && <p className="mt-2 text-xs text-muted-foreground/70 font-mono bg-muted/30 p-2 rounded">{tpl.body}</p>}
  </div>
);

/* ── Trigger Row ── */
const TriggerRow = ({ status, template, icon: Icon, color }) => (
  <div className="flex items-center gap-3 p-3 rounded-lg border border-border/40 bg-card/40">
    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${color}`}>
      <Icon className="w-4 h-4 text-white" />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium">{status}</p>
      <p className="text-xs text-muted-foreground">→ Template: <code className="text-emerald-500">{template}</code></p>
    </div>
    <Zap className="w-4 h-4 text-yellow-500" />
  </div>
);

/* ═══════════ MAIN ═══════════ */
const WhatsAppDashboard = () => {
  const [status, setStatus] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving] = useState(false);
  const [testing, setTesting] = useState(false);

  // Config form — removed for security (server-side only)

  // Test form
  const [testPhone, setTestPhone] = useState('');

  const fetchAll = useCallback(async () => {
    try {
      const [sRes, tRes, lRes] = await Promise.allSettled([
        getWhatsAppStatus(),
        getWhatsAppTemplates(),
        getWhatsAppLogs(),
      ]);
      if (sRes.status === 'fulfilled') setStatus(sRes.value.data);
      if (tRes.status === 'fulfilled') setTemplates(tRes.value.data.templates || []);
      if (lRes.status === 'fulfilled') setLogs(lRes.value.data.logs || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Config is server-side only — no credential inputs

  const handleTestMessage = async () => {
    if (!testPhone) { toast.error('Entrez un numéro de téléphone'); return; }
    setTesting(true);
    try {
      const res = await sendWhatsAppTest({ to_phone: testPhone, template_name: 'hello_world' });
      toast.success(`Message envoyé ! ID: ${res.data.message_id}`);
      fetchAll();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Échec de l\'envoi');
    } finally { setTesting(false); }
  };

  const copyText = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return (
    <div className="flex items-center justify-center h-96">
      <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
    </div>
  );

  return (
    <div className="space-y-6 p-1">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold">WhatsApp Business</h1>
          </div>
          <p className="text-sm text-muted-foreground">Connecteur direct Meta Cloud API — Zéro Coût (1000 conv./mois gratuites)</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge configured={status?.configured} enabled={status?.enabled} />
          <Button variant="outline" size="sm" onClick={fetchAll}><RefreshCw className="w-3.5 h-3.5 mr-1" /> Actualiser</Button>
        </div>
      </div>

      {/* ── Info Banner ── */}
      <motion.div variants={fadeUp} initial="hidden" animate="visible">
        <Card className="border-blue-500/20 bg-blue-500/5">
          <CardContent className="pt-4 pb-4">
            <div className="flex gap-3">
              <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-semibold text-blue-300 mb-1">Comment obtenir votre Token gratuit</p>
                <ol className="list-decimal list-inside space-y-1 text-muted-foreground text-xs">
                  <li>Allez sur <a href="https://developers.facebook.com" target="_blank" rel="noreferrer" className="text-blue-400 underline hover:text-blue-300">developers.facebook.com</a></li>
                  <li>Créez une App → Type: <strong>Business</strong></li>
                  <li>Ajoutez le produit <strong>WhatsApp</strong></li>
                  <li>Dans <strong>API Setup</strong>, copiez le <code className="text-emerald-400">Phone Number ID</code> et le <code className="text-emerald-400">Temporary Access Token</code></li>
                  <li>Collez-les ci-dessous et cliquez "Sauvegarder"</li>
                </ol>
                <p className="mt-2 text-xs text-muted-foreground/70">
                  Le tier gratuit Meta offre <strong className="text-emerald-400">1 000 conversations/mois</strong> sans frais.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── LEFT: Config + Test ── */}
        <div className="lg:col-span-2 space-y-6">

          {/* Config Status (read-only — credentials managed server-side) */}
          <motion.div variants={fadeUp} initial="hidden" animate="visible" transition={{ delay: 0.05 }}>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Settings className="w-4 h-4 text-emerald-500" /> Configuration Meta Cloud API
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                    <p className="text-xs text-muted-foreground mb-1">Phone Number ID</p>
                    <p className="text-sm font-semibold">{status?.phone_id_set
                      ? <span className="text-emerald-600 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Configuré</span>
                      : <span className="text-amber-600 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> Non défini</span>
                    }</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                    <p className="text-xs text-muted-foreground mb-1">Access Token</p>
                    <p className="text-sm font-semibold">{status?.token_set
                      ? <span className="text-emerald-600 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Configuré</span>
                      : <span className="text-amber-600 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> Non défini</span>
                    }</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/30 border border-border/40">
                    <p className="text-xs text-muted-foreground mb-1">Statut</p>
                    <p className="text-sm font-semibold">{status?.configured
                      ? <span className="text-emerald-600">Prêt</span>
                      : <span className="text-amber-600">Non configuré</span>
                    }</p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Endpoint : <code className="text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded text-[10px]">graph.facebook.com/v17.0</code> — Credentials gérées côté serveur (<code>.env</code>)
                </p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Test Message Card */}
          <motion.div variants={fadeUp} initial="hidden" animate="visible" transition={{ delay: 0.1 }}>
            <Card className={!status?.configured ? 'opacity-50 pointer-events-none' : ''}>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Send className="w-4 h-4 text-blue-500" /> 📲 Test Message
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-muted-foreground">Envoie le template <code className="text-emerald-400">hello_world</code> (pré-approuvé par Meta) à un numéro de test.</p>
                <div className="flex gap-3">
                  <div className="relative flex-1">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input value={testPhone} onChange={e => setTestPhone(e.target.value)} placeholder="+213 5XX XXX XXX" className="pl-10" />
                  </div>
                  <Button onClick={handleTestMessage} disabled={testing || !status?.configured} className="bg-blue-600 hover:bg-blue-700 text-white min-w-[140px]">
                    {testing ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Send className="w-4 h-4 mr-1" />}
                    Envoyer Test
                  </Button>
                </div>
                {!status?.configured && (
                  <div className="flex items-center gap-2 text-xs text-yellow-500">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Configurez d'abord votre Phone ID et Access Token ci-dessus.
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Smart Notifications / Triggers */}
          <motion.div variants={fadeUp} initial="hidden" animate="visible" transition={{ delay: 0.15 }}>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Zap className="w-4 h-4 text-yellow-500" /> Smart Notifications (Triggers Automatiques)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground mb-3">Quand le statut d'une commande change, un message WhatsApp est envoyé automatiquement au client.</p>
                <TriggerRow status="En cours de livraison" template="delivery_update" icon={Send} color="bg-blue-500" />
                <TriggerRow status="Livré" template="delivery_confirmed" icon={CheckCircle} color="bg-emerald-500" />
                <div className="mt-3 p-3 rounded-lg bg-muted/30 border border-border/30">
                  <p className="text-xs text-muted-foreground">
                    <strong className="text-foreground">Note :</strong> Les templates <code>delivery_update</code> et <code>delivery_confirmed</code> doivent être créés et approuvés dans votre <a href="https://business.facebook.com/wa/manage/message-templates/" target="_blank" rel="noreferrer" className="text-blue-400 underline">Meta Business Manager</a>. Le template <code>hello_world</code> est pré-approuvé.
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* ── RIGHT: Templates + Logs ── */}
        <div className="space-y-6">
          {/* Templates */}
          <motion.div variants={fadeUp} initial="hidden" animate="visible" transition={{ delay: 0.1 }}>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <MessageCircle className="w-4 h-4 text-emerald-500" /> Templates Disponibles
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {templates.map((tpl, i) => <TemplateCard key={i} tpl={tpl} />)}
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Logs */}
          <motion.div variants={fadeUp} initial="hidden" animate="visible" transition={{ delay: 0.15 }}>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Bell className="w-4 h-4 text-blue-500" /> Derniers Envois
                </CardTitle>
              </CardHeader>
              <CardContent>
                {logs.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-6">Aucun envoi enregistré</p>
                ) : (
                  <div className="space-y-2">
                    {logs.slice(0, 8).map((log, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-muted/20 text-xs">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                        <span className="font-mono truncate">{log.to_phone}</span>
                        <span className="text-muted-foreground ml-auto text-[10px]">{log.template || 'text'}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default WhatsAppDashboard;
