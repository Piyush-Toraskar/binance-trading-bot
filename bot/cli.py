"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from .client import BinanceFuturesClient
from .exceptions import AuthenticationError, TradingBotError
from .logging_config import setup_logging
from .orders import TradingBotService, build_response_summary
from .validators import ValidatedOrderInput, validate_order_inputs

DEFAULT_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading symbol, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument(
        "--order-type",
        required=True,
        dest="order_type",
        help="MARKET or LIMIT",
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", help="Limit price (required for LIMIT orders)")
    parser.add_argument("--api-key", default=os.getenv("BINANCE_API_KEY"))
    parser.add_argument("--api-secret", default=os.getenv("BINANCE_API_SECRET"))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--recv-window", type=int, default=5000)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--log-file", default="logs/trading_bot.log")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the order without sending it to Binance.",
    )
    return parser


def print_request_summary(order: ValidatedOrderInput, *, base_url: str, dry_run: bool) -> None:
    summary = {
        "symbol": order.symbol,
        "side": order.side,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "price": order.price,
        "base_url": base_url,
        "mode": "DRY_RUN" if dry_run else "LIVE_TESTNET",
    }
    print("Order request summary")
    print(json.dumps(summary, indent=2))


def print_response_summary(summary: dict[str, object]) -> None:
    response = {
        "orderId": summary.get("orderId"),
        "status": summary.get("status"),
        "executedQty": summary.get("executedQty"),
        "avgPrice": summary.get("avgPrice") or "N/A",
        "price": summary.get("price") or "N/A",
    }
    print("Order response details")
    print(json.dumps(response, indent=2))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(args.log_file)

    try:
        validated = validate_order_inputs(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )

        if not args.dry_run and (not args.api_key or not args.api_secret):
            raise AuthenticationError(
                "Missing API credentials. Set BINANCE_API_KEY and BINANCE_API_SECRET, or pass --api-key and --api-secret."
            )

        print_request_summary(validated, base_url=args.base_url, dry_run=args.dry_run)

        client = BinanceFuturesClient(
            api_key=args.api_key,
            api_secret=args.api_secret,
            base_url=args.base_url,
            recv_window=args.recv_window,
            timeout=args.timeout,
        )
        service = TradingBotService(client)
        result = service.submit_order(validated, dry_run=args.dry_run)

        if result.get("dry_run"):
            print("Success: input validation passed. No order was sent.")
            return 0

        summary = build_response_summary(result)
        print_response_summary(summary)
        print("Success: order submitted to Binance Futures Testnet.")
        return 0
    except TradingBotError as exc:
        print(f"Failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
