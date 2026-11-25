"""Replay one Monnify-style webhook event against a handler, like a provider retrying.

    python replay.py naive --times 3     # same event, three deliveries
    python replay.py safe --times 3
    python replay.py safe --forge        # wrong signature, like an attacker
    python replay.py reset               # both wallets back to zero
"""
import argparse
import hashlib
import hmac
import json
import os
from decimal import Decimal
from pathlib import Path

import requests

TARGETS = {"naive": "http://127.0.0.1:5000", "safe": "http://127.0.0.1:5001"}
SECRET_KEY = os.environ.get("MONNIFY_SECRET_KEY", "demo-secret-key")
EVENT = Path(__file__).with_name("sample_event.json").read_bytes()


def naira(value) -> str:
    return f"₦{Decimal(value):,.2f}"


def balance(base: str) -> str:
    return naira(requests.get(f"{base}/balance", timeout=5).json()["balance"])


def deliver(base: str, forge: bool) -> requests.Response:
    key = b"not-the-real-secret" if forge else SECRET_KEY.encode()
    signature = hmac.new(key, EVENT, hashlib.sha512).hexdigest()
    return requests.post(
        f"{base}/webhooks/monnify",
        data=EVENT,
        headers={"Content-Type": "application/json", "monnify-signature": signature},
        timeout=5,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", choices=[*TARGETS, "reset"])
    parser.add_argument("--times", type=int, default=1, help="how many times to deliver the same event")
    parser.add_argument("--forge", action="store_true", help="sign with the wrong key")
    args = parser.parse_args()

    if args.target == "reset":
        for name, base in TARGETS.items():
            requests.post(f"{base}/reset", timeout=5)
            print(f"{name:5}  wallet reset to {balance(base)}")
        return

    base = TARGETS[args.target]
    data = json.loads(EVENT)["eventData"]
    print(f"event  {data['transactionReference']}  {naira(data['amountPaid'])}")
    for attempt in range(1, args.times + 1):
        r = deliver(base, args.forge)
        label = "forged" if args.forge else f"delivery {attempt}"
        print(f"{label:11} -> {r.status_code}  {r.text if r.ok else 'rejected'}")
    print(f"wallet balance: {balance(base)}")


if __name__ == "__main__":
    main()
