"""
Swingbot — automated swing trading bot template.

Usage:
    python swingbot.py --mode scan      # read-only, log signals
    python swingbot.py --mode enter     # place orders for new signals
    python swingbot.py --mode manage    # close positions hitting stops/targets

Configuration in config.yaml. Strategy logic in strategy.py.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

import strategy
from broker import Broker
from notifications import notify

BASE = Path(__file__).parent
CONFIG_FILE = BASE / "config.yaml"
STATE_FILE = BASE / "state" / "positions.json"

ALPACA_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY")


def load_config() -> dict:
    with CONFIG_FILE.open() as f:
        return yaml.safe_load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def position_size(account_value: float, entry: float, stop: float,
                  risk_pct: float) -> int:
    risk_dollars = account_value * (risk_pct / 100.0)
    risk_per_share = abs(entry - stop)
    if risk_per_share <= 0:
        return 0
    return int(risk_dollars / risk_per_share)


def scan(broker: Broker, config: dict, state: dict, do_enter: bool) -> None:
    watchlist = config.get("watchlist", [])
    risk_pct = config.get("risk_pct_per_trade", 1.0)
    account_value = broker.get_account_value()
    open_positions = broker.get_open_positions()

    notify(
        f"=== SCAN @ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Account: ${account_value:,.2f} | Open: {len(open_positions)}"
    )

    signals_found = 0
    for symbol in watchlist:
        if symbol in open_positions:
            print(f"  · {symbol}: position open, skipping")
            continue

        bars = broker.get_bars(symbol)
        if bars is None or len(bars) < 60:
            print(f"  ! {symbol}: insufficient bars")
            continue

        signal = strategy.evaluate(symbol, bars, config.get("strategy", {}))
        if signal is None:
            print(f"  · {symbol}: no signal")
            continue

        signals_found += 1
        qty = position_size(account_value, signal.entry, signal.stop, risk_pct)
        if qty <= 0:
            print(f"  ! {symbol}: position size 0 — skipping")
            continue

        msg = (
            f"📊 SIGNAL | {symbol} {signal.bias.upper()} | "
            f"entry=${signal.entry:.2f} stop=${signal.stop:.2f} "
            f"target=${signal.target:.2f} qty={qty} R:R={signal.rr:.1f}"
        )

        if do_enter:
            try:
                side = "buy" if signal.bias == "bullish" else "sell"
                order = broker.place_market(symbol, qty, side)
                state[symbol] = {
                    "entered_at": datetime.now(timezone.utc).isoformat(),
                    "bias": signal.bias,
                    "entry": signal.entry,
                    "stop": signal.stop,
                    "target": signal.target,
                    "qty": qty,
                    "order_id": str(order.id),
                }
                notify(f"✅ EXECUTED | {msg}")
            except Exception as e:
                notify(f"❌ FAILED to enter {symbol}: {e}")
        else:
            notify(msg)

    if signals_found == 0:
        notify("No signals on this scan.")


def manage(broker: Broker, state: dict) -> None:
    open_positions = broker.get_open_positions()
    notify(
        f"=== MANAGE @ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Open: {len(open_positions)}"
    )

    for symbol, pos in open_positions.items():
        record = state.get(symbol)
        if not record:
            print(f"  ? {symbol}: open but no record")
            continue

        bars = broker.get_bars(symbol, days=2)
        if bars is None or bars.empty:
            continue
        last = float(bars["close"].iloc[-1])
        bias = record["bias"]
        stop = record["stop"]
        target = record["target"]

        hit_stop = (bias == "bullish" and last <= stop) or \
                   (bias == "bearish" and last >= stop)
        hit_target = (bias == "bullish" and last >= target) or \
                     (bias == "bearish" and last <= target)

        if hit_stop or hit_target:
            reason = "stop" if hit_stop else "target"
            try:
                broker.close_position(symbol)
                state.pop(symbol, None)
                notify(f"🚪 CLOSED | {symbol} @ ${last:.2f} ({reason})")
            except Exception as e:
                notify(f"❌ FAILED to close {symbol}: {e}")
        else:
            print(f"  · {symbol}: holding @ ${last:.2f}")


def main() -> int:
    if not (ALPACA_KEY and ALPACA_SECRET):
        print("ALPACA_API_KEY and ALPACA_SECRET_KEY required", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["scan", "enter", "manage"],
                        default="scan")
    args = parser.parse_args()

    config = load_config()
    state = load_state()
    broker = Broker(ALPACA_KEY, ALPACA_SECRET, paper=True)

    if args.mode == "scan":
        scan(broker, config, state, do_enter=False)
    elif args.mode == "enter":
        scan(broker, config, state, do_enter=True)
    elif args.mode == "manage":
        manage(broker, state)

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
