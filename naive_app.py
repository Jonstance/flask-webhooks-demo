"""The handler most of us write first. Don't ship this.

It trusts whatever arrives and credits the wallet on every call,
so a retried or forged event moves money again.
"""
from flask import request

from models import add_to_wallet, create_app, db

app = create_app(__name__, "naive.db")


@app.post("/webhooks/monnify")
def monnify_webhook():
    event = request.get_json()
    data = event["eventData"]

    add_to_wallet(data["amountPaid"])
    db.session.commit()
    return "credited", 200


if __name__ == "__main__":
    app.run(port=5000)
