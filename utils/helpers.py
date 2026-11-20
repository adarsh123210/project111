"""
Utility modules for authentication, formatting, charge calculation, and tracking IDs.
"""

import hashlib
import random
import re
from datetime import datetime


def hash_password(password: str) -> str:
    """Hash a plaintext password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Check if the provided password matches the stored hash."""
    return hash_password(password) == hashed_password


def generate_tracking_number() -> str:
    """Generate a unique tracking number in CMS-YYYY-XXXXXX format."""
    year = datetime.now().year
    random_digits = random.randint(100000, 999999)
    return f"CMS-{year}-{random_digits}"


def validate_phone(phone: str) -> bool:
    """Validate 10-digit phone number or basic standard format."""
    cleaned = re.sub(r"[^\d]", "", phone)
    return len(cleaned) >= 10


def validate_email(email: str) -> bool:
    """Validate email pattern."""
    if not email:
        return True
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))


def copy_to_clipboard(root, text: str):
    """Copy given text to Windows system clipboard."""
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()  # keeps clipboard after app is unfocused
        return True
    except Exception:
        return False


def calculate_delivery_cost(parcel_type: str, weight_kg: float, is_express: bool = False, distance_km: float = 50.0, charge_rules: list = None) -> dict:

    """
    Calculate delivery charges based on rules.
    Returns breakdown dict.
    """
    rule = None
    if charge_rules:
        for r in charge_rules:
            if r.get("parcel_type", "").lower() == parcel_type.lower():
                rule = r
                break

    base_charge = rule["base_charge"] if rule else 50.0
    per_kg = rule["per_kg_rate"] if rule else 15.0
    per_km = rule["per_km_rate"] if rule else 0.5
    multiplier = rule["express_multiplier"] if (rule and is_express) else (1.5 if is_express else 1.0)

    weight_cost = max(0.0, float(weight_kg)) * per_kg
    distance_cost = max(0.0, float(distance_km)) * per_km
    subtotal = base_charge + weight_cost + distance_cost
    total = subtotal * (multiplier if is_express else 1.0)

    return {
        "base_charge": round(base_charge, 2),
        "weight_cost": round(weight_cost, 2),
        "distance_cost": round(distance_cost, 2),
        "express_surcharge": round((subtotal * multiplier) - subtotal, 2) if is_express else 0.0,
        "total": round(total, 2),
    }
