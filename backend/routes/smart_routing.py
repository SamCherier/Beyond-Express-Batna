from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import math
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== ALGERIAN WILAYA COORDINATES =====
# Approximate centroids for the 58 wilayas
WILAYA_COORDS = {
    "Adrar": (27.87, -0.29), "Chlef": (36.17, 1.33), "Laghouat": (33.80, 2.88),
    "Oum El Bouaghi": (35.88, 7.11), "Batna": (35.56, 6.17), "Bejaia": (36.75, 5.08),
    "Biskra": (34.85, 5.73), "Bechar": (31.62, -2.22), "Blida": (36.47, 2.83),
    "Bouira": (36.38, 3.90), "Tamanrasset": (22.79, 5.53), "Tebessa": (35.40, 8.12),
    "Tlemcen": (34.88, -1.31), "Tiaret": (35.37, 1.32), "Tizi Ouzou": (36.72, 4.05),
    "Alger": (36.75, 3.04), "Djelfa": (34.67, 3.25), "Jijel": (36.82, 5.77),
    "Setif": (36.19, 5.41), "Saida": (34.84, 0.15), "Skikda": (36.88, 6.91),
    "Sidi Bel Abbes": (35.19, -0.63), "Annaba": (36.90, 7.77), "Guelma": (36.46, 7.43),
    "Constantine": (36.37, 6.61), "Medea": (36.26, 2.75), "Mostaganem": (35.93, 0.09),
    "M'Sila": (35.71, 4.54), "Mascara": (35.40, 0.14), "Ouargla": (31.95, 5.33),
    "Oran": (35.70, -0.63), "El Bayadh": (33.68, 1.02), "Illizi": (26.51, 8.47),
    "Bordj Bou Arreridj": (36.07, 4.76), "Boumerdes": (36.76, 3.47),
    "El Tarf": (36.77, 8.31), "Tindouf": (27.67, -8.15), "Tissemsilt": (35.61, 1.81),
    "El Oued": (33.37, 6.86), "Khenchela": (35.43, 7.14), "Souk Ahras": (36.29, 7.95),
    "Tipaza": (36.59, 2.44), "Mila": (36.45, 6.26), "Ain Defla": (36.26, 1.97),
    "Naama": (33.27, -0.31), "Ain Temouchent": (35.30, -1.14), "Ghardaia": (32.49, 3.67),
    "Relizane": (35.74, 0.56), "Sétif": (36.19, 5.41), "Béjaïa": (36.75, 5.08),
    "Béchar": (31.62, -2.22),
}

SOUTH_WILAYAS = {
    "Adrar", "Tamanrasset", "Illizi", "Bechar", "Béchar",
    "Tindouf", "El Oued", "Ghardaia", "Ouargla", "Laghouat",
    "El Bayadh", "Naama", "Biskra", "Djelfa"
}


# ===== HAVERSINE FORMULA =====
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ===== MODELS =====
class DeliveryPoint(BaseModel):
    id: str
    customer_name: str
    address: str
    wilaya: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class DriverLocation(BaseModel):
    lat: float
    lng: float
    wilaya: str

class OptimizeRequest(BaseModel):
    driver_location: DriverLocation
    deliveries: List[DeliveryPoint]

class OptimizedStop(BaseModel):
    stop_number: int
    delivery: DeliveryPoint
    distance_km: float
    estimated_minutes: int
    same_wilaya: bool


# ===== ROUTE OPTIMIZATION =====
def optimize_route(driver: DriverLocation, deliveries: List[DeliveryPoint]) -> List[OptimizedStop]:
    """
    Proximity-based route optimization:
    1. Same-wilaya deliveries first
    2. Then sort by Haversine distance (nearest-neighbour greedy)
    """
    if not deliveries:
        return []

    driver_lat, driver_lng = driver.lat, driver.lng

    # Resolve coordinates from wilaya if not provided
    resolved = []
    for d in deliveries:
        lat = d.lat
        lng = d.lng
        if lat is None or lng is None:
            coords = WILAYA_COORDS.get(d.wilaya)
            if coords:
                lat, lng = coords
            else:
                lat, lng = 36.75, 3.04  # Default to Algiers
        resolved.append((d, lat, lng))

    # Greedy nearest-neighbour with same-wilaya priority
    remaining = list(resolved)
    route = []
    current_lat, current_lng = driver_lat, driver_lng

    while remaining:
        best_idx = 0
        best_score = float('inf')
        for i, (d, lat, lng) in enumerate(remaining):
            dist = haversine_km(current_lat, current_lng, lat, lng)
            # Same-wilaya bonus: reduce effective distance by 50%
            if d.wilaya == driver.wilaya:
                dist *= 0.5
            if dist < best_score:
                best_score = dist
                best_idx = i

        chosen_d, chosen_lat, chosen_lng = remaining.pop(best_idx)
        actual_dist = haversine_km(current_lat, current_lng, chosen_lat, chosen_lng)
        # Average speed 35km/h in urban Algeria
        est_minutes = max(5, int((actual_dist / 35) * 60))

        route.append(OptimizedStop(
            stop_number=len(route) + 1,
            delivery=chosen_d,
            distance_km=round(actual_dist, 1),
            estimated_minutes=est_minutes,
            same_wilaya=chosen_d.wilaya == driver.wilaya
        ))
        current_lat, current_lng = chosen_lat, chosen_lng

    return route


# ===== API ENDPOINTS =====

@router.post("/optimize")
async def optimize_delivery_route(data: OptimizeRequest):
    """Optimize delivery route using proximity-based algorithm"""
    optimized = optimize_route(data.driver_location, data.deliveries)
    
    total_distance = sum(s.distance_km for s in optimized)
    total_time = sum(s.estimated_minutes for s in optimized)
    
    return {
        "optimized_route": [s.model_dump() for s in optimized],
        "total_distance_km": round(total_distance, 1),
        "total_estimated_minutes": total_time,
        "stops_count": len(optimized),
        "algorithm": "proximity_nearest_neighbour"
    }


@router.get("/wilayas")
async def get_wilayas_with_coords():
    """Return all wilayas with their coordinates"""
    return [
        {"name": name, "lat": lat, "lng": lng, "is_south": name in SOUTH_WILAYAS}
        for name, (lat, lng) in WILAYA_COORDS.items()
    ]
