"""
Status Mapper - Unified Status Normalization
Maps carrier-specific statuses to standardized internal statuses

Master Statuses:
  - PENDING (Gris) - Commande créée, en attente
  - PREPARING (Orange) - En préparation
  - READY_TO_SHIP (Jaune) - Prêt à expédier
  - PICKED_UP (Bleu clair) - Récupéré par le transporteur
  - IN_TRANSIT (Bleu) - En transit, au centre de tri
  - OUT_FOR_DELIVERY (Violet) - En cours de livraison
  - DELIVERED (Vert) - Livré, encaissé
  - FAILED (Orange foncé) - Échec de livraison
  - RETURNED (Rouge) - Retourné à l'expéditeur
  - CANCELLED (Gris foncé) - Annulé
"""
from enum import Enum
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MasterStatus(str, Enum):
    """Standardized internal statuses"""
    PENDING = "pending"
    PREPARING = "preparing"
    READY_TO_SHIP = "ready_to_ship"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"
    CANCELLED = "cancelled"


# Status metadata (color, label, icon, order)
STATUS_META: Dict[MasterStatus, Dict] = {
    MasterStatus.PENDING: {
        "color": "#6B7280",  # Gray
        "bg_color": "#F3F4F6",
        "label": "En attente",
        "label_ar": "قيد الانتظار",
        "icon": "⏳",
        "order": 0
    },
    MasterStatus.PREPARING: {
        "color": "#F59E0B",  # Orange
        "bg_color": "#FEF3C7",
        "label": "En préparation",
        "label_ar": "قيد التحضير",
        "icon": "📦",
        "order": 1
    },
    MasterStatus.READY_TO_SHIP: {
        "color": "#EAB308",  # Yellow
        "bg_color": "#FEF9C3",
        "label": "Prêt à expédier",
        "label_ar": "جاهز للشحن",
        "icon": "✅",
        "order": 2
    },
    MasterStatus.PICKED_UP: {
        "color": "#06B6D4",  # Cyan
        "bg_color": "#CFFAFE",
        "label": "Récupéré",
        "label_ar": "تم الاستلام",
        "icon": "🚛",
        "order": 3
    },
    MasterStatus.IN_TRANSIT: {
        "color": "#3B82F6",  # Blue
        "bg_color": "#DBEAFE",
        "label": "En transit",
        "label_ar": "في الطريق",
        "icon": "🚚",
        "order": 4
    },
    MasterStatus.OUT_FOR_DELIVERY: {
        "color": "#8B5CF6",  # Purple
        "bg_color": "#EDE9FE",
        "label": "En cours de livraison",
        "label_ar": "قيد التوصيل",
        "icon": "🏃",
        "order": 5
    },
    MasterStatus.DELIVERED: {
        "color": "#10B981",  # Green
        "bg_color": "#D1FAE5",
        "label": "Livré",
        "label_ar": "تم التوصيل",
        "icon": "✅",
        "order": 6
    },
    MasterStatus.FAILED: {
        "color": "#F97316",  # Orange dark
        "bg_color": "#FFEDD5",
        "label": "Échec livraison",
        "label_ar": "فشل التوصيل",
        "icon": "⚠️",
        "order": 7
    },
    MasterStatus.RETURNED: {
        "color": "#EF4444",  # Red
        "bg_color": "#FEE2E2",
        "label": "Retourné",
        "label_ar": "مرتجع",
        "icon": "↩️",
        "order": 8
    },
    MasterStatus.CANCELLED: {
        "color": "#4B5563",  # Gray dark
        "bg_color": "#E5E7EB",
        "label": "Annulé",
        "label_ar": "ملغى",
        "icon": "❌",
        "order": 9
    }
}


# Yalidine status mapping
YALIDINE_STATUS_MAP: Dict[str, MasterStatus] = {
    # French statuses
    "En préparation": MasterStatus.PREPARING,
    "Prêt à expédier": MasterStatus.READY_TO_SHIP,
    "Expédié": MasterStatus.PICKED_UP,
    "Expédié vers le centre": MasterStatus.IN_TRANSIT,
    "Reçu au centre": MasterStatus.IN_TRANSIT,
    "En cours de livraison": MasterStatus.OUT_FOR_DELIVERY,
    "En attente du client": MasterStatus.OUT_FOR_DELIVERY,
    "Livré": MasterStatus.DELIVERED,
    "Echec livraison": MasterStatus.FAILED,
    "Échec livraison": MasterStatus.FAILED,
    "Retour en cours": MasterStatus.RETURNED,
    "Retourné": MasterStatus.RETURNED,
    "Annulé": MasterStatus.CANCELLED,
    # English aliases
    "Preparing": MasterStatus.PREPARING,
    "Ready": MasterStatus.READY_TO_SHIP,
    "Shipped": MasterStatus.PICKED_UP,
    "In Transit": MasterStatus.IN_TRANSIT,
    "Out for Delivery": MasterStatus.OUT_FOR_DELIVERY,
    "Delivered": MasterStatus.DELIVERED,
    "Failed": MasterStatus.FAILED,
    "Returned": MasterStatus.RETURNED,
    "Cancelled": MasterStatus.CANCELLED,
}


# ZR Express status mapping
ZR_EXPRESS_STATUS_MAP: Dict[str, MasterStatus] = {
    # English statuses (typical for ZR)
    "REGISTERED": MasterStatus.PREPARING,
    "PENDING": MasterStatus.PENDING,
    "PICKED_UP": MasterStatus.PICKED_UP,
    "IN_TRANSIT": MasterStatus.IN_TRANSIT,
    "AT_HUB": MasterStatus.IN_TRANSIT,
    "OUT_FOR_DELIVERY": MasterStatus.OUT_FOR_DELIVERY,
    "DELIVERED": MasterStatus.DELIVERED,
    "FAILED": MasterStatus.FAILED,
    "RETURN_TO_SENDER": MasterStatus.RETURNED,
    "RETURNED": MasterStatus.RETURNED,
    "CANCELLED": MasterStatus.CANCELLED,
    # French aliases
    "Enregistré": MasterStatus.PREPARING,
    "En attente": MasterStatus.PENDING,
    "Récupéré": MasterStatus.PICKED_UP,
    "En transit": MasterStatus.IN_TRANSIT,
    "Au hub": MasterStatus.IN_TRANSIT,
    "En livraison": MasterStatus.OUT_FOR_DELIVERY,
    "Livré": MasterStatus.DELIVERED,
    "Échoué": MasterStatus.FAILED,
    "Retour expéditeur": MasterStatus.RETURNED,
    "Retourné": MasterStatus.RETURNED,
    "Annulé": MasterStatus.CANCELLED,
}


# DHD Express status mapping
DHD_STATUS_MAP: Dict[str, MasterStatus] = {
    "Nouveau": MasterStatus.PENDING,
    "Pris en charge": MasterStatus.PICKED_UP,
    "En cours": MasterStatus.IN_TRANSIT,
    "En livraison": MasterStatus.OUT_FOR_DELIVERY,
    "Livré": MasterStatus.DELIVERED,
    "Non livré": MasterStatus.FAILED,
    "Retour": MasterStatus.RETURNED,
}


# Carrier mapping registry
CARRIER_STATUS_MAPS = {
    "yalidine": YALIDINE_STATUS_MAP,
    "zr_express": ZR_EXPRESS_STATUS_MAP,
    "dhd": DHD_STATUS_MAP,
}


def normalize_status(
    carrier_raw_status: str,
    carrier_type: str = "yalidine"
) -> MasterStatus:
    """
    Normalize a carrier-specific status to our internal MasterStatus
    
    Args:
        carrier_raw_status: Raw status string from carrier API
        carrier_type: Type of carrier (yalidine, zr_express, dhd, etc.)
        
    Returns:
        MasterStatus enum value
    """
    if not carrier_raw_status:
        return MasterStatus.PENDING
    
    # Get the appropriate mapping
    status_map = CARRIER_STATUS_MAPS.get(carrier_type, YALIDINE_STATUS_MAP)
    
    # Try exact match first
    if carrier_raw_status in status_map:
        return status_map[carrier_raw_status]
    
    # Try case-insensitive match
    raw_lower = carrier_raw_status.lower().strip()
    for key, value in status_map.items():
        if key.lower() == raw_lower:
            return value
    
    # Try partial match
    for key, value in status_map.items():
        if raw_lower in key.lower() or key.lower() in raw_lower:
            return value
    
    # Default fallback based on keywords
    raw_lower = carrier_raw_status.lower()
    
    if any(kw in raw_lower for kw in ["livr", "deliver", "توصيل"]):
        return MasterStatus.DELIVERED
    if any(kw in raw_lower for kw in ["retour", "return", "مرتجع"]):
        return MasterStatus.RETURNED
    if any(kw in raw_lower for kw in ["transit", "route", "طريق"]):
        return MasterStatus.IN_TRANSIT
    if any(kw in raw_lower for kw in ["échec", "fail", "فشل"]):
        return MasterStatus.FAILED
    if any(kw in raw_lower for kw in ["annul", "cancel", "ملغى"]):
        return MasterStatus.CANCELLED
    
    logger.warning(f"⚠️ Unknown status '{carrier_raw_status}' for carrier {carrier_type}")
    return MasterStatus.PENDING


def get_status_meta(status: MasterStatus) -> Dict:
    """Get metadata for a status (color, label, icon)"""
    return STATUS_META.get(status, STATUS_META[MasterStatus.PENDING])


def get_status_label(status: MasterStatus, lang: str = "fr") -> str:
    """Get localized label for a status"""
    meta = get_status_meta(status)
    if lang == "ar":
        return meta.get("label_ar", meta["label"])
    return meta["label"]


def get_status_color(status: MasterStatus) -> Tuple[str, str]:
    """Get color and background color for a status"""
    meta = get_status_meta(status)
    return (meta["color"], meta["bg_color"])


def get_status_icon(status: MasterStatus) -> str:
    """Get emoji icon for a status"""
    return get_status_meta(status).get("icon", "📦")


def get_status_order(status: MasterStatus) -> int:
    """Get sort order for a status (for timeline display)"""
    return get_status_meta(status).get("order", 0)


def is_final_status(status: MasterStatus) -> bool:
    """Check if a status is final (no more updates expected)"""
    return status in [
        MasterStatus.DELIVERED,
        MasterStatus.RETURNED,
        MasterStatus.CANCELLED
    ]


def get_next_status_simulation(current_status: MasterStatus) -> MasterStatus:
    """
    Get the next status in a typical progression (for simulation/demo)
    
    Used for ZR Express mock to simulate status advancement
    """
    progression = [
        MasterStatus.PENDING,
        MasterStatus.PREPARING,
        MasterStatus.READY_TO_SHIP,
        MasterStatus.PICKED_UP,
        MasterStatus.IN_TRANSIT,
        MasterStatus.OUT_FOR_DELIVERY,
        MasterStatus.DELIVERED
    ]
    
    try:
        current_index = progression.index(current_status)
        if current_index < len(progression) - 1:
            return progression[current_index + 1]
    except ValueError:
        pass
    
    return current_status  # Return same if already at end or not in progression
