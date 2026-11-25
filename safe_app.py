"""The same handler, answering the gateman's questions before it gives value.

1. Who sent this?        -> verify the HMAC-SHA512 signature on the raw body
2. Has it come before?   -> let a unique key in the database reject duplicates

In production, also do question 3: reply 200 fast, then confirm the payment
with the provider's transaction status API in a background job before giving
value (see the talk slides). It's left out here so the demo runs offline.
"""
import hashlib
import hmac
import json
import os

from flask import abort, request
from sqlalchemy.exc import IntegrityError

from models import ProcessedEvent, add_to_wallet, create_app, db

SECRET_KEY = os.environ.get("MONNIFY_SECRET_KEY", "demo-secret-key")

app = create_app(__name__, "safe.db")


@app.post("/webhooks/monnify")
def monnify_webhook():
    # 1. Who sent this? Hash the raw bytes, not request.json.
    raw = request.get_data()
    expected = hmac.new(SECRET_KEY.encode(), raw, hashlib.sha512).hexdigest()
    received = request.headers.get("monnify-signature", "")
    if not hmac.compare_digest(expected, received):
        abort(401)

    event = json.loads(raw)
    data = event["eventData"]
    if event.get("eventType") != "SUCCESSFUL_TRANSACTION":
        return "ignored", 200

    # 2. Has it come before? Record the reference and credit in ONE transaction,
    #    so a crash can't leave an event marked done but never credited.
    try:
        db.session.add(ProcessedEvent(reference=data["transactionReference"]))
        add_to_wallet(data["amountPaid"])
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return "duplicate, ignored", 200

    return "credited", 200


if __name__ == "__main__":
    app.run(port=5001)
