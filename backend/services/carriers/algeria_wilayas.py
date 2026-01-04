"""
Algeria Wilayas Database
Mapping between wilaya names and IDs for Yalidine API

Yalidine uses numeric IDs for wilayas (1-58)
This module provides conversion utilities
"""

# Complete list of 58 Algeria wilayas with IDs
WILAYAS = {
    "Adrar": 1,
    "Chlef": 2,
    "Laghouat": 3,
    "Oum El Bouaghi": 4,
    "Batna": 5,
    "Béjaïa": 6,
    "Bejaia": 6,
    "Biskra": 7,
    "Béchar": 8,
    "Bechar": 8,
    "Blida": 9,
    "Bouira": 10,
    "Tamanrasset": 11,
    "Tébessa": 12,
    "Tebessa": 12,
    "Tlemcen": 13,
    "Tiaret": 14,
    "Tizi Ouzou": 15,
    "Alger": 16,
    "Algiers": 16,
    "Djelfa": 17,
    "Jijel": 18,
    "Sétif": 19,
    "Setif": 19,
    "Saïda": 20,
    "Saida": 20,
    "Skikda": 21,
    "Sidi Bel Abbès": 22,
    "Sidi Bel Abbes": 22,
    "Annaba": 23,
    "Guelma": 24,
    "Constantine": 25,
    "Médéa": 26,
    "Medea": 26,
    "Mostaganem": 27,
    "M'Sila": 28,
    "M'sila": 28,
    "Msila": 28,
    "Mascara": 29,
    "Ouargla": 30,
    "Oran": 31,
    "El Bayadh": 32,
    "Illizi": 33,
    "Bordj Bou Arréridj": 34,
    "Bordj Bou Arreridj": 34,
    "BBA": 34,
    "Boumerdès": 35,
    "Boumerdes": 35,
    "El Tarf": 36,
    "Tindouf": 37,
    "Tissemsilt": 38,
    "El Oued": 39,
    "Khenchela": 40,
    "Souk Ahras": 41,
    "Tipaza": 42,
    "Mila": 43,
    "Aïn Defla": 44,
    "Ain Defla": 44,
    "Naâma": 45,
    "Naama": 45,
    "Aïn Témouchent": 46,
    "Ain Temouchent": 46,
    "Ghardaïa": 47,
    "Ghardaia": 47,
    "Relizane": 48,
    # New wilayas (added 2019)
    "Timimoun": 49,
    "Bordj Badji Mokhtar": 50,
    "Ouled Djellal": 51,
    "Béni Abbès": 52,
    "Beni Abbes": 52,
    "In Salah": 53,
    "In Guezzam": 54,
    "Touggourt": 55,
    "Djanet": 56,
    "El M'Ghair": 57,
    "El Mghair": 57,
    "El Meniaa": 58,
}

# Reverse mapping: ID to name
WILAYAS_BY_ID = {
    1: "Adrar",
    2: "Chlef",
    3: "Laghouat",
    4: "Oum El Bouaghi",
    5: "Batna",
    6: "Béjaïa",
    7: "Biskra",
    8: "Béchar",
    9: "Blida",
    10: "Bouira",
    11: "Tamanrasset",
    12: "Tébessa",
    13: "Tlemcen",
    14: "Tiaret",
    15: "Tizi Ouzou",
    16: "Alger",
    17: "Djelfa",
    18: "Jijel",
    19: "Sétif",
    20: "Saïda",
    21: "Skikda",
    22: "Sidi Bel Abbès",
    23: "Annaba",
    24: "Guelma",
    25: "Constantine",
    26: "Médéa",
    27: "Mostaganem",
    28: "M'Sila",
    29: "Mascara",
    30: "Ouargla",
    31: "Oran",
    32: "El Bayadh",
    33: "Illizi",
    34: "Bordj Bou Arréridj",
    35: "Boumerdès",
    36: "El Tarf",
    37: "Tindouf",
    38: "Tissemsilt",
    39: "El Oued",
    40: "Khenchela",
    41: "Souk Ahras",
    42: "Tipaza",
    43: "Mila",
    44: "Aïn Defla",
    45: "Naâma",
    46: "Aïn Témouchent",
    47: "Ghardaïa",
    48: "Relizane",
    49: "Timimoun",
    50: "Bordj Badji Mokhtar",
    51: "Ouled Djellal",
    52: "Béni Abbès",
    53: "In Salah",
    54: "In Guezzam",
    55: "Touggourt",
    56: "Djanet",
    57: "El M'Ghair",
    58: "El Meniaa",
}


def normalize_wilaya_name(name: str) -> str:
    """Normalize wilaya name for matching"""
    if not name:
        return ""
    # Remove accents and normalize
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c',
        "'": " ", "-": " ", "_": " "
    }
    result = name.lower().strip()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def get_wilaya_id(wilaya_name: str) -> int:
    """
    Convert wilaya name to Yalidine ID
    
    Args:
        wilaya_name: Name of the wilaya (e.g., "Alger", "Batna", "Tizi Ouzou")
        
    Returns:
        Wilaya ID (1-58) or 16 (Alger) as default
    """
    if not wilaya_name:
        return 16  # Default to Alger
    
    # Direct match first
    if wilaya_name in WILAYAS:
        return WILAYAS[wilaya_name]
    
    # Try normalized match
    normalized = normalize_wilaya_name(wilaya_name)
    
    for name, wid in WILAYAS.items():
        if normalize_wilaya_name(name) == normalized:
            return wid
    
    # Partial match
    for name, wid in WILAYAS.items():
        if normalized in normalize_wilaya_name(name) or normalize_wilaya_name(name) in normalized:
            return wid
    
    # Default to Alger
    return 16


def get_wilaya_name(wilaya_id: int) -> str:
    """
    Convert Yalidine wilaya ID to name
    
    Args:
        wilaya_id: Wilaya ID (1-58)
        
    Returns:
        Wilaya name
    """
    return WILAYAS_BY_ID.get(wilaya_id, "Alger")


def is_valid_wilaya(wilaya_name: str) -> bool:
    """Check if a wilaya name is valid"""
    if not wilaya_name:
        return False
    
    normalized = normalize_wilaya_name(wilaya_name)
    
    for name in WILAYAS.keys():
        if normalize_wilaya_name(name) == normalized:
            return True
    
    return False
