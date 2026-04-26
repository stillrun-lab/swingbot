"""
Example strategy: SMA crossover with ATR-based risk management.

To use a different strategy, replace the body of evaluate() — keep the
signature the same. Return a Signal when conditions trigger, or None.
"""
from dataclasses import dataclass

import pandas as pd


@dataclass
class Signal:
    symbol: str
    bias: str          # "bullish" or "bearish"
    entry: float
    stop: float
    target: float
    rr: float


def evaluate(symbol: str, bars: pd.DataFrame, config: dict) -> Signal | None:
    """
    bars:   DataFrame with columns [open, high, low, close, volume]
            indexed by datetime, oldest to newest.
    config: strategy section from config.yaml
    Returns: Signal on fresh crossover, else None.
    """
    fast = config.get("sma_fast", 20)
    slow = config.get("sma_slow", 50)
    rr = config.get("risk_reward", 2.0)
    atr_mult = config.get("atr_stop_mult", 1.5)

    if len(bars) < slow + 5:
        return None

    sma_fast = bars["close"].rolling(fast).mean()
    sma_slow = bars["close"].rolling(slow).mean()

    just_crossed_up = (sma_fast.iloc[-1] > sma_slow.iloc[-1] and
                       sma_fast.iloc[-2] <= sma_slow.iloc[-2])
    just_crossed_down = (sma_fast.iloc[-1] < sma_slow.iloc[-1] and
                         sma_fast.iloc[-2] >= sma_slow.iloc[-2])

    if not (just_crossed_up or just_crossed_down):
        return None

    entry = float(bars["close"].iloc[-1])
    atr = float((bars["high"] - bars["low"]).rolling(14).mean().iloc[-1])

    if just_crossed_up:
        stop = entry - atr * atr_mult
        target = entry + (entry - stop) * rr
        return Signal(symbol, "bullish", entry, stop, target, rr)
    else:
        stop = entry + atr * atr_mult
        target = entry - (stop - entry) * rr
        return Signal(symbol, "bearish", entry, stop, target, rr)
