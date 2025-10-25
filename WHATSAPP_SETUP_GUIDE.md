# Module WhatsApp + AI Agent - Guide de Configuration

## 📋 Vue d'Ensemble

Le module WhatsApp intègre un **AI Agent GPT-4o** qui gère automatiquement les conversations clients via WhatsApp Business API (Twilio). L'agent peut:

- 🔍 Suivre des commandes par numéro de suivi
- ✅ Confirmer des commandes
- ❌ Annuler des commandes
- 🌐 Répondre en FR/AR/EN automatiquement
- 👤 Transférer vers un agent humain si nécessaire

---

## 🚀 Configuration Twilio WhatsApp

### Étape 1: Créer un Compte Twilio

1. **Visitez** [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. **Inscrivez-vous** avec votre email
3. **Vérifiez** votre numéro de téléphone
4. **Complétez** le questionnaire (sélectionnez "WhatsApp" comme produit)

### Étape 2: Obtenir vos Credentials

Une fois connecté au Dashboard Twilio:

#### A. Account SID & Auth Token
1. Allez sur votre **Dashboard** principal
2. Trouvez la section **"Account Info"**
3. Notez:
   - **Account SID** (commence par `AC...`)
   - **Auth Token** (cliquez sur "Show" pour révéler)

   ![Twilio Dashboard](https://www.twilio.com/docs/usage/tutorials/images/account-sid-auth-token.png)

#### B. WhatsApp Sandbox (pour les tests)

Twilio propose un sandbox WhatsApp gratuit pour tester avant d'avoir un numéro approuvé:

1. Dans le menu gauche: **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Vous verrez le numéro de sandbox Twilio (ex: `+1 415 523 8886`)
3. **Activez votre WhatsApp**: 
   - Sur votre téléphone, ouvrez WhatsApp
   - Ajoutez le numéro Twilio comme contact
   - Envoyez le code fourni (ex: "join [code]")
   - Vous recevrez une confirmation

**Numéro à utiliser**: `whatsapp:+14155238886` (ou celui affiché dans votre sandbox)

#### C. WhatsApp Business API (Production)

Pour utiliser votre propre numéro WhatsApp Business en production:

1. **Demander un numéro**: 
   - Menu: **Messaging** → **Services** → **WhatsApp**
   - Cliquez sur **"Request to enable your Twilio numbers for WhatsApp"**
   - Remplissez le formulaire de demande

2. **Processus d'approbation**:
   - Twilio examinera votre demande (1-2 jours)
   - Vous devez avoir un compte WhatsApp Business vérifié
   - Frais: ~$3-5/mois par numéro

3. **Alternative**: Acheter un numéro Twilio WhatsApp-enabled
   - Menu: **Phone Numbers** → **Buy a Number**
   - Filtrez par "WhatsApp" capability
   - Prix: variable selon pays/région

### Étape 3: Configurer les Webhooks

Les webhooks permettent à Twilio d'envoyer les messages entrants vers votre application:

1. Dans Twilio Console: **Messaging** → **Settings** → **WhatsApp sandbox settings**

2. Configurez les URLs de webhook:

   **a. Webhook URL pour messages entrants:**
   ```
   https://your-domain.emergentagent.com/api/whatsapp/webhook/incoming
   ```
   - Method: `POST`

   **b. Status callback URL (optionnel):**
   ```
   https://your-domain.emergentagent.com/api/whatsapp/webhook/status
   ```
   - Method: `POST`

3. **Important**: Pour le développement local, utilisez **ngrok**:
   ```bash
   ngrok http 8001
   ```
   Puis utilisez l'URL ngrok fournie (ex: `https://abc123.ngrok.io/api/whatsapp/webhook/incoming`)

### Étape 4: Ajouter les Credentials dans Beyond Express

1. **Connectez-vous** au serveur où Beyond Express est installé

2. **Éditez** le fichier `.env` du backend:
   ```bash
   nano /app/backend/.env
   ```

3. **Remplacez** les placeholders par vos vraies valeurs:
   ```env
   # Twilio WhatsApp Configuration
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_actual_auth_token_here
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   WEBHOOK_BASE_URL=https://your-domain.emergentagent.com
   ```

4. **Redémarrez** le backend:
   ```bash
   sudo supervisorctl restart backend
   ```

5. **Vérifiez** les logs:
   ```bash
   tail -f /var/log/supervisor/backend.err.log
   ```
   Vous devriez voir:
   ```
   ✅ Twilio client initialized successfully
   ✅ AI Agent initialized with Emergent LLM Key
   ```

---

## 🧪 Tester l'Intégration

### Test 1: Envoyer un Message Depuis l'Application

1. **Créez une commande** avec un numéro WhatsApp valide (format: +213...)
2. **Cochez** "Envoyer une confirmation WhatsApp automatiquement"
3. **Validez** → Vous devriez recevoir un message WhatsApp

### Test 2: Message Entrant + Réponse AI

1. **Depuis WhatsApp**, envoyez un message au numéro Twilio:
   ```
   Bonjour
   ```

2. **L'AI devrait répondre**:
   ```
   Bonjour! 👋 Je suis l'assistant Beyond Express.
   
   Comment puis-je vous aider aujourd'hui?
   ```

3. **Testez le suivi**:
   ```
   Où est ma commande TRK123456?
   ```

4. **L'AI devrait chercher** et répondre avec les détails ou transférer à un humain

### Test 3: Dashboard WhatsApp

1. **Ouvrez** `/dashboard/whatsapp`
2. **Vérifiez** que les conversations apparaissent
3. **Cliquez** sur une conversation
4. **Testez** "Prendre le relais"
5. **Envoyez** un message manuel

---

## ⚙️ Configuration Avancée

### Personnaliser les Prompts AI

Éditez `/app/backend/utils/ai_prompts.py` pour modifier:
- Le ton de l'AI
- Les instructions de comportement
- Les templates de réponse
- La détection d'intentions

### Ajouter des Templates de Messages

Dans `/app/backend/services/twilio_service.py`, créez de nouveaux templates:

```python
def send_delivery_notification(self, to_phone, order_id, tracking_id):
    message_body = f"""🚚 Votre colis est en route!
    
    📦 Commande: {order_id}
    🔢 Suivi: {tracking_id}
    
    Livraison prévue: demain
    Merci! 🎉"""
    
    return self.send_whatsapp_message(to_phone, message_body)
```

### Limites et Quotas Twilio

**Sandbox (Gratuit)**:
- Limite: 500 messages/mois
- Destinataires: Doivent rejoindre le sandbox manuellement

**Production**:
- Frais: ~$0.005-0.01 par message selon destination
- Pas de limite de messages
- Templates pré-approuvés requis pour certains cas

---

## 🐛 Dépannage

### Erreur: "Twilio not configured"

**Cause**: Credentials manquants ou invalides

**Solution**:
1. Vérifiez que `.env` contient les bonnes valeurs
2. Redémarrez le backend
3. Vérifiez les logs

### Messages non reçus

**Vérifiez**:
1. Le numéro est au format E.164 (`+213...`)
2. Le numéro a rejoint le sandbox Twilio
3. Les webhooks sont configurés
4. Twilio Console → Monitor → Logs pour voir les erreurs

### AI ne répond pas

**Vérifiez**:
1. `EMERGENT_LLM_KEY` est configuré
2. Backend logs pour erreurs GPT-4o
3. Le webhook incoming est accessible (testez avec ngrok)

### Erreur CORS

**Solution**: Vérifiez que `WEBHOOK_BASE_URL` dans `.env` correspond à l'URL publique

---

## 📊 Surveillance et Logs

### Logs Backend
```bash
# Voir tous les logs
tail -f /var/log/supervisor/backend.err.log

# Filtrer WhatsApp
tail -f /var/log/supervisor/backend.err.log | grep -i whatsapp

# Filtrer AI
tail -f /var/log/supervisor/backend.err.log | grep -i "AI\|GPT"
```

### Twilio Console Monitoring
- **Monitor** → **Logs** → **Errors** pour voir les échecs
- **Messaging** → **Logs** pour l'historique complet

---

## 💡 Bonnes Pratiques

1. **Toujours tester** avec le sandbox avant la production
2. **Surveiller** les quotas Twilio pour éviter les surcharges
3. **Configurer des alertes** Twilio pour les erreurs critiques
4. **Sauvegarder** régulièrement la base MongoDB (conversations importantes)
5. **Mettre à jour** les prompts AI selon les retours clients

---

## 📞 Support

**Twilio Support**: https://support.twilio.com
**Emergent Support**: contact@emergentagent.com
**Documentation Twilio WhatsApp**: https://www.twilio.com/docs/whatsapp

---

## ✅ Checklist de Déploiement

- [ ] Compte Twilio créé et vérifié
- [ ] Credentials (Account SID, Auth Token) obtenus
- [ ] Numéro WhatsApp activé (Sandbox ou Business)
- [ ] Webhooks configurés avec URL publique
- [ ] `.env` mis à jour avec les credentials
- [ ] Backend redémarré
- [ ] Test envoi message (création commande)
- [ ] Test réception message (webhook)
- [ ] Test Dashboard WhatsApp
- [ ] Test prise en charge humaine
- [ ] Monitoring activé

**Une fois tous les éléments cochés, votre module WhatsApp + AI Agent est opérationnel !** 🚀
