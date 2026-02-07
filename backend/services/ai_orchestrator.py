"""
AI Orchestrator — Multi-Agent Brain Center
Uses Groq SDK (AsyncGroq) for ultra-fast LPU inference.
Falls back to realistic simulation when no API key is set.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ── Master System Prompt ──

MASTER_SYSTEM_PROMPT = (
    "Tu es un Senior Logistics Analyst chez Beyond Express, "
    "expert en optimisation de stock, routage de livraisons et analyse "
    "opérationnelle pour le marché algérien (58 wilayas). "
    "Tu fournis des recommandations chiffrées, actionnables et en français. "
    "Tu connais les spécificités géographiques de l'Algérie (distance, terrain, "
    "zones urbaines vs rurales) et les contraintes des transporteurs locaux "
    "(Yalidine, ZR Express, DHD). "
    "Tes réponses doivent toujours inclure des métriques, des pourcentages "
    "et des actions concrètes."
)

# ── Agent Definitions ──

AGENTS = {
    "logistician": {
        "id": "logistician",
        "name": "Le Logisticien",
        "model_hint": "Qwen 2.5",
        "icon": "truck",
        "color": "#3B82F6",
        "description": "Optimisation des routes, packaging et capacité entrepôt",
        "system_prompt": (
            f"{MASTER_SYSTEM_PROMPT}\n\n"
            "Spécialisation : optimisation des routes de livraison, "
            "bin-packing 3D et gestion de capacité d'entrepôt."
        ),
    },
    "analyst": {
        "id": "analyst",
        "name": "L'Analyste",
        "model_hint": "Llama 3.3",
        "icon": "bar-chart",
        "color": "#8B5CF6",
        "description": "Analyse de données, documents, tendances et prévisions",
        "system_prompt": (
            f"{MASTER_SYSTEM_PROMPT}\n\n"
            "Spécialisation : analyse de données logistiques, lecture de documents/"
            "factures, production d'insights chiffrés et recommandations stratégiques."
        ),
    },
    "monitor": {
        "id": "monitor",
        "name": "Le Moniteur",
        "model_hint": "Mixtral",
        "icon": "terminal",
        "color": "#10B981",
        "description": "Surveillance des erreurs, alertes système et santé plateforme",
        "system_prompt": (
            f"{MASTER_SYSTEM_PROMPT}\n\n"
            "Spécialisation : ingénierie DevOps/SRE — surveillance des logs d'erreurs, "
            "santé du système, métriques de performance, détection d'anomalies."
        ),
    },
}

# ── Simulated Responses (demo mode) ──

SIMULATED_RESPONSES = {
    "logistician": {
        "stock_analysis": (
            "Analyse terminée en 2.3s.\n\n"
            "**Résultats d'optimisation :**\n"
            "- Zone A2 (Sèche) : occupation 85% → recommandation de redistribuer "
            "15 unités vers Zone B2 (Standard, 85%)\n"
            "- Gain estimé : **+12% d'espace** en Zone A2\n"
            "- Zone Froide A1 : 68% — capacité confortable\n\n"
            "**Actions recommandées :**\n"
            "1. Transférer les colis non-périssables de A2 → B2\n"
            "2. Réorganiser les étagères 3-7 en Zone A2 (layout en U)\n"
            "3. Planifier un inventaire Zone B1 (Fragile) ce week-end"
        ),
        "route_optimization": (
            "Optimisation de tournée calculée.\n\n"
            "**Résumé :**\n"
            "- Distance originale : 142 km\n"
            "- Distance optimisée : **118 km** (-17%)\n"
            "- Temps estimé : 3h20 → **2h45** (-18%)\n"
            "- Économie carburant : ~4.2L de diesel\n\n"
            "**Stratégie :**\n"
            "1. Regrouper les livraisons par wilaya (same-wilaya first)\n"
            "2. Éviter le centre-ville d'Alger entre 8h-10h\n"
            "3. Livraisons Constantine en bloc (3 colis adjacents)"
        ),
        "default": (
            "Analyse logistique en cours...\n\n"
            "**Recommandations :**\n"
            "- Taux d'utilisation global : 78.4% — dans la zone optimale\n"
            "- Prochaine action : surveiller Constantine (91% capacité)\n"
            "- Prévision J+7 : besoin de +50 emplacements à Alger"
        ),
    },
    "analyst": {
        "performance_report": (
            "Rapport de performance généré.\n\n"
            "**KPIs du mois :**\n"
            "- Livraisons réussies : 89.2% (+3.1% vs mois dernier)\n"
            "- Délai moyen : 2.4 jours (-0.3j)\n"
            "- Retours : 8.7% (objectif : <10% ✓)\n"
            "- Chiffre d'affaires : 162,250 DA (+23%)\n\n"
            "**Tendances :**\n"
            "- Pic de commandes : Mardi-Jeudi\n"
            "- Wilaya la plus active : Oran (28% des volumes)\n"
            "- Motif retour #1 : Client Absent (38%)"
        ),
        "default": (
            "Analyse de données terminée.\n\n"
            "**Insights :**\n"
            "- 18 commandes actives, 5 livrées, 3 en transit\n"
            "- Revenu moyen par colis : 9,014 DA\n"
            "- Top client : 4 commandes récurrentes\n"
            "- Recommandation : offrir livraison gratuite au-dessus de 5,000 DA"
        ),
    },
    "monitor": {
        "health_check": (
            "Diagnostic système complet.\n\n"
            "**Santé de la plateforme :**\n"
            "- API Backend : ✅ Opérationnel (latence moy. 45ms)\n"
            "- Base de données : ✅ MongoDB connecté (4 collections actives)\n"
            "- Authentification : ✅ Argon2id + Sessions\n"
            "- Audit Log : ✅ Chaîne de hash intègre\n\n"
            "**Alertes :**\n"
            "- ⚠️ 153 sessions obsolètes nettoyées\n"
            "- ⚠️ Entrepôt Constantine à 91% — seuil d'alerte\n"
            "- ✅ Aucune erreur 500 dans les dernières 24h"
        ),
        "default": (
            "Surveillance en cours...\n\n"
            "**État :**\n"
            "- Uptime : 99.97% (30 derniers jours)\n"
            "- Requêtes/min : 12.4 (normal)\n"
            "- Erreurs récentes : 0 critiques, 2 warnings (CORS)\n"
            "- Prochaine maintenance : aucune planifiée"
        ),
    },
}


class AIOrchestrator:
    """Central brain that routes requests to the appropriate agent via Groq SDK."""

    def __init__(self):
        self.api_key: Optional[str] = None
        self.provider: str = "simulation"
        self.enabled: bool = True
        self.model: str = "llama-3.3-70b-versatile"
        self._groq_client = None
        self._load_config()

    def _load_config(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        if self.api_key:
            self.provider = "groq"
            self._init_groq_client()

    def _init_groq_client(self):
        """Initialize the AsyncGroq client."""
        if not self.api_key:
            self._groq_client = None
            return
        try:
            from groq import AsyncGroq
            self._groq_client = AsyncGroq(api_key=self.api_key)
            logger.info(f"✅ Groq client initialized (model: {self.model})")
        except Exception as e:
            logger.error(f"❌ Failed to init Groq client: {e}")
            self._groq_client = None

    def configure(self, api_key: Optional[str] = None, provider: str = "groq",
                  model: str = "llama-3.3-70b-versatile", enabled: bool = True):
        if api_key:
            self.api_key = api_key
        self.provider = provider if self.api_key else "simulation"
        self.model = model
        self.enabled = enabled
        if self.api_key:
            self._init_groq_client()
        else:
            self._groq_client = None

    @property
    def is_live(self) -> bool:
        return bool(self.api_key) and self.provider != "simulation" and self._groq_client is not None

    def get_status(self) -> dict:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "is_live": self.is_live,
            "has_api_key": bool(self.api_key),
            "agents": list(AGENTS.values()),
        }

    async def query_agent(self, agent_id: str, task: str, context: dict = None) -> dict:
        if agent_id not in AGENTS:
            return {"error": f"Agent '{agent_id}' not found"}

        agent = AGENTS[agent_id]

        if self.is_live:
            return await self._query_groq(agent, task, context)
        else:
            return self._query_simulated(agent, task, context)

    def _query_simulated(self, agent: dict, task: str, context: dict = None) -> dict:
        agent_id = agent["id"]
        responses = SIMULATED_RESPONSES.get(agent_id, {})

        task_lower = task.lower()
        matched_key = "default"
        for key in responses:
            if key != "default" and key.replace("_", " ") in task_lower:
                matched_key = key
                break
        if matched_key == "default":
            if any(w in task_lower for w in ["stock", "entrepôt", "warehouse", "capacité", "espace"]):
                matched_key = "stock_analysis"
            elif any(w in task_lower for w in ["route", "tournée", "livraison", "trajet"]):
                matched_key = "route_optimization"
            elif any(w in task_lower for w in ["performance", "kpi", "rapport", "chiffre"]):
                matched_key = "performance_report"
            elif any(w in task_lower for w in ["santé", "health", "erreur", "log", "système"]):
                matched_key = "health_check"

        response_text = responses.get(matched_key, responses.get("default", "Analyse en cours..."))

        return {
            "agent": agent["name"],
            "agent_id": agent["id"],
            "model": f"{agent['model_hint']} (Simulation)",
            "response": response_text,
            "is_simulated": True,
            "task": task,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _query_groq(self, agent: dict, task: str, context: dict = None) -> dict:
        """Live query using the Groq SDK (AsyncGroq)."""
        try:
            completion = await self._groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": agent["system_prompt"]},
                    {"role": "user", "content": task},
                ],
                temperature=0.7,
                max_tokens=1024,
            )

            return {
                "agent": agent["name"],
                "agent_id": agent["id"],
                "model": self.model,
                "response": completion.choices[0].message.content,
                "is_simulated": False,
                "task": task,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "usage": {
                    "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if completion.usage else 0,
                },
            }

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            result = self._query_simulated(agent, task, context)
            result["fallback"] = True
            result["error"] = str(e)
            return result


# Singleton
orchestrator = AIOrchestrator()
