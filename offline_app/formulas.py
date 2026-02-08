from __future__ import annotations

from typing import Any, Dict, Tuple

DEFAULT_DATA: Dict[str, Any] = {
    "customer_name": "",
    "order_number": "",
    "product": "",
    "quantity": 0.0,
    "price": 0.0,
    "region": "local",
    "delivery": "standard",
    "urgent": False,
    "notes": "",
}

REGIONS = {"local", "national", "international"}
DELIVERY_TYPES = {"standard", "express"}
DELIVERY_FEES: Dict[Tuple[str, str], float] = {
    ("local", "standard"): 5.0,
    ("local", "express"): 15.0,
    ("national", "standard"): 12.0,
    ("national", "express"): 25.0,
    ("international", "standard"): 30.0,
    ("international", "express"): 60.0,
}


def _parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _round_money(value: float) -> float:
    return round(value + 1e-9, 2)


def normalize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, default_value in DEFAULT_DATA.items():
        result[key] = data.get(key, default_value)

    result["customer_name"] = str(result["customer_name"] or "").strip()
    result["order_number"] = str(result["order_number"] or "").strip()
    result["product"] = str(result["product"] or "").strip()
    result["notes"] = str(result["notes"] or "").strip()

    result["quantity"] = max(0.0, _parse_float(result["quantity"], 0.0))
    result["price"] = max(0.0, _parse_float(result["price"], 0.0))
    result["urgent"] = _parse_bool(result["urgent"])

    region = str(result["region"] or "").strip().lower()
    delivery = str(result["delivery"] or "").strip().lower()
    result["region"] = region if region in REGIONS else DEFAULT_DATA["region"]
    result["delivery"] = (
        delivery if delivery in DELIVERY_TYPES else DEFAULT_DATA["delivery"]
    )

    return result


def compute_results(data: Dict[str, Any]) -> Dict[str, Any]:
    quantity = max(0.0, _parse_float(data.get("quantity"), 0.0))
    price = max(0.0, _parse_float(data.get("price"), 0.0))
    subtotal = quantity * price

    if quantity >= 100:
        discount_rate = 0.15
    elif quantity >= 50:
        discount_rate = 0.10
    elif quantity >= 10:
        discount_rate = 0.05
    else:
        discount_rate = 0.0

    discount_amount = subtotal * discount_rate
    delivery_fee = DELIVERY_FEES.get(
        (data.get("region", "local"), data.get("delivery", "standard")), 0.0
    )
    urgent_fee = 10.0 if _parse_bool(data.get("urgent")) else 0.0

    tax_rate = 0.2 if data.get("region") != "international" else 0.0
    taxable = max(0.0, subtotal - discount_amount) + delivery_fee + urgent_fee
    tax_amount = taxable * tax_rate
    total = taxable + tax_amount

    status = "ok"
    if quantity <= 0 or price <= 0:
        status = "missing_values"

    return {
        "subtotal": _round_money(subtotal),
        "discount_rate": discount_rate,
        "discount_amount": _round_money(discount_amount),
        "delivery_fee": _round_money(delivery_fee),
        "urgent_fee": _round_money(urgent_fee),
        "tax_rate": tax_rate,
        "tax_amount": _round_money(tax_amount),
        "total": _round_money(total),
        "status": status,
    }
