import pytest

from flyalpha.actions import TradingAction
from flyalpha.exchanges import OrderRequest, PaperExchangeClient
from flyalpha.trading_loop import run_trading_once


def test_paper_exchange_records_order():
    exchange = PaperExchangeClient(last_price=123.0)

    order = exchange.place_order(OrderRequest(symbol="BTCUSD", side="buy", quantity=0.1))

    assert order.status == "filled"
    assert order.fill_price == 123.0
    assert exchange.orders == [order]


def test_paper_trading_tick_can_place_simulated_order():
    result = run_trading_once(
        mode="paper",
        symbol="BTCUSD",
        action=TradingAction.LONG,
        quantity=0.1,
    )

    assert result.order is not None
    assert result.order.side == "buy"


def test_live_trade_requires_confirmation():
    with pytest.raises(RuntimeError, match="live order blocked"):
        run_trading_once(
            mode="live",
            symbol="BTCUSD",
            action=TradingAction.LONG,
            quantity=0.1,
            base_url="https://example.invalid",
        )

