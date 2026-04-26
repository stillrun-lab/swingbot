# Swingbot

Customizable swing trading bot template. Scans a watchlist on a schedule,
evaluates a pluggable strategy, posts signals to Telegram + Discord, and
optionally executes paper trades on Alpaca. Built to be cloned, customized,
and deployed in under an hour.

## What it does

For each symbol in `config.yaml`, swingbot fetches daily bars, runs the
strategy module's `evaluate()` function, and reports signals. In `scan`
mode (the default) it just notifies. In `enter` mode it sizes the position
based on configured risk and submits a market order. In `manage` mode it
checks open positions for stop or target hits and closes them.

```yaml
# Example config.yaml
watchlist: [SPY, QQQ, AAPL, MSFT, NVDA]
risk_pct_per_trade: 1.0
strategy:
  sma_fast: 20
  sma_slow: 50
  atr_stop_mult: 1.5
  risk_reward: 2.0
```

## Architecture

```
┌──────────────────────┐
│ GitHub Actions cron  │   open + pre-close
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────┐
│ swingbot.py (orchestration)      │
│  --mode scan  | enter | manage   │
└──┬─────────┬────────────┬────────┘
   │         │            │
   ▼         ▼            ▼
config    strategy.py  broker.py
.yaml     (signals)    (Alpaca)
                          │
                          ▼
                       Alpaca
                       (paper)
            ┌─────────────┘
            ▼
       notifications.py
            │
   ┌────────┴────────┐
   ▼                 ▼
Telegram         Discord
```

Modular by design — `strategy.py` is the only file you need to touch to
plug in a different system (RSI divergence, Bollinger bands, ICT setups,
machine-learning signals — anything that returns a `Signal` or `None`).

## Modes

| Mode      | Behavior                                                      |
|-----------|---------------------------------------------------------------|
| `scan`    | Read-only — fetches bars, evaluates strategy, notifies        |
| `enter`   | Scan + submits Alpaca paper market orders for new signals     |
| `manage`  | Checks open positions for stop/target hits, closes them       |

The included workflow runs `scan` by default. To go live, change `--mode scan`
to `--mode enter` in `.github/workflows/cycle.yml` and add a separate
manage cycle if desired.

## Safety

- Defaults to `paper=True` on Alpaca — no live brokerage by default
- Default cycle is `scan` only — won't place orders without explicit opt-in
- Position sizing risk is capped via `risk_pct_per_trade` in config
- All actions logged to GitHub Actions output and notified to Telegram

## Quick start

1. Fork or clone this repo
2. Edit `config.yaml` with your watchlist and strategy parameters
3. Set repo secrets:
   - `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` from [alpaca.markets](https://alpaca.markets) (free paper account)
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - `DISCORD_WEBHOOK_URL` (optional)
4. Commit and push
5. Run the workflow manually first to verify — should report scan results to Telegram

## Custom builds

Need this extended — different broker (IBKR, Tradier, TradeStation), live
brokerage execution, advanced indicators, multi-timeframe analysis, custom
risk management, Claude-reviewed signal filtering, multi-account routing?
I build production trading systems for retail traders, prop desks, and
algorithmic firms.

**Built by [Stillrun Lab](https://github.com/stillrun-lab)** — automation systems built to run themselves.

- 💼 Hire me on Upwork: *(link coming soon)*
- 🐦 [@trade_4l on X](https://x.com/trade_4l)
- 📧 *(email coming soon)*

## Disclaimer

This is template code for educational and paper-trading purposes. It does
not constitute financial advice. The included strategy is illustrative;
backtest and paper-trade extensively before deploying capital.
