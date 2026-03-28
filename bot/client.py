"""Thin Binance Futures REST client."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Mapping
from urllib.parse import urlencode

import requests

from .exceptions import AuthenticationError, BinanceAPIError, NetworkError


class BinanceFuturesClient:
    def __init__(
        self,
        *,
        api_key: str | None,
        api_secret: str | None,
        base_url: str,
        recv_window: int = 5000,
        timeout: int = 20,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.recv_window = recv_window
        self.timeout = timeout
        self.session = session or requests.Session()
        self.logger = logging.getLogger(__name__)

    def _signed_params(self, params: Mapping[str, Any]) -> dict[str, Any]:
        if not self.api_key or not self.api_secret:
            raise AuthenticationError(
                "API key and secret are required to place live orders."
            )

        payload = {k: v for k, v in params.items() if v is not None}
        payload["recvWindow"] = self.recv_window
        payload["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(payload, doseq=True)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        payload["signature"] = signature
        return payload

    @staticmethod
    def _sanitise_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
        clean = dict(params or {})
        if "signature" in clean:
            clean["signature"] = "***masked***"
        return clean

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        signed: bool = False,
    ) -> Any:
        url = f"{self.base_url}{path}"
        prepared_params = dict(params or {})
        headers: dict[str, str] = {}

        if signed:
            prepared_params = self._signed_params(prepared_params)
            headers["X-MBX-APIKEY"] = self.api_key or ""

        self.logger.info(
            "API request",
            extra={
                "event_data": {
                    "method": method.upper(),
                    "url": url,
                    "params": self._sanitise_params(prepared_params),
                }
            },
        )

        try:
            if method.upper() == "GET":
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=prepared_params,
                    headers=headers,
                    timeout=self.timeout,
                )
            else:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    data=prepared_params,
                    headers=headers,
                    timeout=self.timeout,
                )
        except requests.RequestException as exc:
            self.logger.exception(
                "Network request failed",
                extra={
                    "event_data": {
                        "method": method.upper(),
                        "url": url,
                    }
                },
            )
            raise NetworkError(f"Network error while calling Binance: {exc}") from exc

        try:
            body: Any = response.json()
        except ValueError:
            body = {"raw": response.text}

        self.logger.info(
            "API response",
            extra={
                "event_data": {
                    "method": method.upper(),
                    "url": url,
                    "status_code": response.status_code,
                    "body": body,
                }
            },
        )

        if response.status_code >= 400:
            raise BinanceAPIError.from_response(response.status_code, body)

        if isinstance(body, dict) and "code" in body and isinstance(body.get("code"), int) and body.get("code", 0) < 0:
            raise BinanceAPIError.from_response(response.status_code, body)

        return body

    def ping(self) -> Any:
        return self._request("GET", "/fapi/v1/ping")

    def get_exchange_info(self) -> Any:
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def place_order(self, params: Mapping[str, Any]) -> Any:
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def query_order(self, symbol: str, order_id: int | str) -> Any:
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )
