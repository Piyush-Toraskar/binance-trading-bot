"""Custom exceptions for the trading bot."""

from __future__ import annotations

from typing import Any


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""


class ValidationError(TradingBotError):
    """Raised when user input is invalid."""


class AuthenticationError(TradingBotError):
    """Raised when API credentials are missing or invalid."""


class NetworkError(TradingBotError):
    """Raised when the Binance API cannot be reached."""


class BinanceAPIError(TradingBotError):
    """Raised when Binance returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        status_code: int | None = None,
        payload: Any | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.payload = payload
        super().__init__(message)

    @classmethod
    def from_response(cls, status_code: int, payload: Any) -> "BinanceAPIError":
        if isinstance(payload, dict):
            code = payload.get("code")
            msg = payload.get("msg") or payload.get("message") or str(payload)
        else:
            code = None
            msg = str(payload)
        return cls(msg, code=code, status_code=status_code, payload=payload)
