"""Alpaca paper-trading client wrapper."""
from datetime import datetime, timedelta, timezone

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


class Broker:
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.trading = TradingClient(api_key, secret_key, paper=paper)
        self.data = StockHistoricalDataClient(api_key, secret_key)

    def get_bars(self, symbol: str, days: int = 100):
        end = datetime.now(timezone.utc) - timedelta(minutes=15)
        start = end - timedelta(days=days)
        req = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
        )
        df = self.data.get_stock_bars(req).df
        if df.empty:
            return None
        if hasattr(df.index, "levels"):
            df = df.xs(symbol, level=0)
        return df[["open", "high", "low", "close", "volume"]]

    def get_account_value(self) -> float:
        return float(self.trading.get_account().equity)

    def get_open_positions(self) -> dict:
        return {
            p.symbol: {
                "qty": int(float(p.qty)),
                "side": "long" if float(p.qty) > 0 else "short",
                "avg_entry": float(p.avg_entry_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
            }
            for p in self.trading.get_all_positions()
        }

    def place_market(self, symbol: str, qty: int, side: str):
        side_enum = OrderSide.BUY if side == "buy" else OrderSide.SELL
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side_enum,
            time_in_force=TimeInForce.DAY,
        )
        return self.trading.submit_order(order)

    def close_position(self, symbol: str):
        return self.trading.close_position(symbol)
