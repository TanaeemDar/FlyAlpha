"""Generic REST exchange adapter scaffold.

This adapter is intentionally conservative. Each real exchange should subclass
or configure it with exact endpoint paths and authentication rules from that
exchange's official API docs.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .base import Balance, Order, OrderRequest, Ticker


@dataclass(frozen=True)
class RestExchangeClient:
    """Small JSON REST client for API-based exchange adapters."""

    base_url: str
    api_key_env: str = "FLYALPHA_EXCHANGE_API_KEY"
    api_secret_env: str = "FLYALPHA_EXCHANGE_API_SECRET"
    timeout_seconds: float = 10.0

    @property
    def api_key(self) -> str:
        return os.getenv(self.api_key_env, "")

    @property
    def api_secret(self) -> str:
        return os.getenv(self.api_secret_env, "")

    def get_ticker(self, symbol: str) -> Ticker:
        payload = self._request("GET", "/ticker", {"symbol": symbol})
        return Ticker(
            symbol=symbol,
            bid=float(payload.get("bid", payload.get("last", 0.0))),
            ask=float(payload.get("ask", payload.get("last", 0.0))),
            last=float(payload.get("last", 0.0)),
        )

    def get_balance(self, asset: str) -> Balance:
        payload = self._request("GET", "/balance", {"asset": asset}, authenticated=True)
        return Balance(
            asset=asset,
            free=float(payload.get("free", 0.0)),
            total=float(payload.get("total", payload.get("free", 0.0))),
        )

    def place_order(self, request: OrderRequest) -> Order:
        payload = self._request(
            "POST",
            "/order",
            {
                "symbol": request.symbol,
                "side": request.side,
                "quantity": request.quantity,
                "type": request.order_type,
            },
            authenticated=True,
        )
        return Order(
            order_id=str(payload.get("order_id", payload.get("id", ""))),
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            status=str(payload.get("status", "submitted")),
            fill_price=float(payload["fill_price"]) if "fill_price" in payload else None,
        )

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, object],
        authenticated: bool = False,
    ) -> dict[str, object]:
        if authenticated and not self.api_key:
            raise RuntimeError(f"missing API key env var: {self.api_key_env}")

        url = self.base_url.rstrip("/") + path
        data = None
        headers = {"Accept": "application/json"}
        if authenticated:
            headers["X-API-KEY"] = self.api_key
        if method == "GET":
            url = f"{url}?{urllib.parse.urlencode(params)}"
        else:
            data = json.dumps(params).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url=url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

