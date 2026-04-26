"""Telegram + Discord webhook notifications. Graceful no-op if creds absent."""
import os
import sys

import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")


def send_telegram(msg: str) -> None:
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT, "text": msg[:4000]},
            timeout=10,
        )
    except Exception as e:
        print(f"  ! telegram failed: {e}", file=sys.stderr)


def send_discord(msg: str) -> None:
    if not DISCORD_WEBHOOK:
        return
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg[:1900]}, timeout=10)
    except Exception as e:
        print(f"  ! discord failed: {e}", file=sys.stderr)


def notify(msg: str) -> None:
    print(msg)
    send_telegram(msg)
    send_discord(msg)
