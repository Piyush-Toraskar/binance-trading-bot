"""Validation helpers for CLI input."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from .exceptions import ValidationError

_ALLOWED_SIDES = {"BUY", "SELL"}
_ALLOWED_ORDER_TYPES = {"MARKET", "LIMIT"}
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


@dataclass(frozen=True)
class ValidatedOrderInput:
    symbol: str
    side: str
    order_type: str
    quantity: str
    price: Optional[str] = None


def _to_positive_decimal(value: str, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number.") from exc

    if decimal_value <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")
    return decimal_value


def decimal_to_api_string(value: Decimal) -> str:
    normalised = format(value.normalize(), "f")
    if "." in normalised:
        normalised = normalised.rstrip("0").rstrip(".")
    return normalised or "0"


def validate_symbol(symbol: str) -> str:
    if not symbol:
        raise ValidationError("symbol is required.")
    cleaned = symbol.strip().upper()
    if not _SYMBOL_PATTERN.match(cleaned):
        raise ValidationError(
            "symbol must be uppercase letters/numbers only, for example BTCUSDT."
        )
    return cleaned


def validate_side(side: str) -> str:
    if not side:
        raise ValidationError("side is required.")
    cleaned = side.strip().upper()
    if cleaned not in _ALLOWED_SIDES:
        raise ValidationError("side must be BUY or SELL.")
    return cleaned


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValidationError("order type is required.")
    cleaned = order_type.strip().upper()
    if cleaned not in _ALLOWED_ORDER_TYPES:
        raise ValidationError("order type must be MARKET or LIMIT.")
    return cleaned


def validate_order_inputs(
    *,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
) -> ValidatedOrderInput:
    valid_symbol = validate_symbol(symbol)
    valid_side = validate_side(side)
    valid_order_type = validate_order_type(order_type)
    valid_quantity = decimal_to_api_string(_to_positive_decimal(quantity, "quantity"))

    valid_price: Optional[str] = None
    if valid_order_type == "LIMIT":
        if price in (None, ""):
            raise ValidationError("price is required for LIMIT orders.")
        valid_price = decimal_to_api_string(_to_positive_decimal(price, "price"))
    elif price not in (None, ""):
        raise ValidationError("price must only be provided for LIMIT orders.")

    return ValidatedOrderInput(
        symbol=valid_symbol,
        side=valid_side,
        order_type=valid_order_type,
        quantity=valid_quantity,
        price=valid_price,
    )
