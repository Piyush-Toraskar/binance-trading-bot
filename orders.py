"""Order placement logic."""

from __future__ import annotations

import logging
import time
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from typing import Any

from .client import BinanceFuturesClient
from .exceptions import BinanceAPIError
from .validators import ValidatedOrderInput


class TradingBotService:
    def __init__(self, client: BinanceFuturesClient) -> None:
        self.client = client
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def build_order_params(order: ValidatedOrderInput) -> dict[str, Any]:
        params: dict[str, Any] = {
            "symbol": order.symbol,
            "side": order.side,
            "type": order.order_type,
            "quantity": order.quantity,
        }
        if order.order_type == "LIMIT":
            params["timeInForce"] = "GTC"
            params["price"] = order.price
        return params

    def submit_order(self, order: ValidatedOrderInput, *, dry_run: bool = False) -> dict[str, Any]:
        request_payload = self.build_order_params(order)

        if dry_run:
            self.logger.info(
                "Dry run requested; order not sent",
                extra={"event_data": {"request": request_payload}},
            )
            return {
                "request": request_payload,
                "create_response": None,
                "order": None,
                "dry_run": True,
            }

        create_response = self.client.place_order(request_payload)
        order_snapshot = None

        order_id = create_response.get("orderId")
        if order_id is not None:
            for attempt in range(2):
                try:
                    if attempt:
                        time.sleep(0.75)
                    order_snapshot = self.client.query_order(order.symbol, order_id)
                    break
                except BinanceAPIError as exc:
                    self.logger.warning(
                        "Could not refresh order details yet",
                        extra={
                            "event_data": {
                                "orderId": order_id,
                                "attempt": attempt + 1,
                                "error": str(exc),
                            }
                        },
                    )

        return {
            "request": request_payload,
            "create_response": create_response,
            "order": order_snapshot or create_response,
            "dry_run": False,
        }


def compute_average_price(order_data: dict[str, Any]) -> str | None:
    avg_price = order_data.get("avgPrice")
    if avg_price not in (None, "", "0", "0.0", "0.00", "0.00000000"):
        return str(avg_price)

    executed_qty = order_data.get("executedQty")
    cum_quote = order_data.get("cumQuote")
    if executed_qty in (None, "", "0", "0.0") or cum_quote in (None, "", "0", "0.0"):
        return None

    try:
        average = Decimal(str(cum_quote)) / Decimal(str(executed_qty))
    except (InvalidOperation, ZeroDivisionError):
        return None
    return format(average.normalize(), "f")


def build_response_summary(result: dict[str, Any]) -> dict[str, Any]:
    order_data = result.get("order") or result.get("create_response") or {}
    return {
        "orderId": order_data.get("orderId"),
        "status": order_data.get("status", "UNKNOWN"),
        "executedQty": order_data.get("executedQty", "0"),
        "avgPrice": compute_average_price(order_data),
        "price": order_data.get("price") or result.get("request", {}).get("price"),
        "symbol": order_data.get("symbol") or result.get("request", {}).get("symbol"),
        "side": order_data.get("side") or result.get("request", {}).get("side"),
        "type": order_data.get("type") or result.get("request", {}).get("type"),
        "raw": order_data,
    }
