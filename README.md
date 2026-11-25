# Idempotent by Design: demo code

Companion code for **"Idempotent by Design: Production-Grade Payment Webhooks in Flask"**, a talk at FlaskCon Africa 2026 (Lagos, 19 December 2026) by Constance Etiosa.

Two Flask apps receive the same Monnify-style payment webhook:

- `naive_app.py` trusts the payload and credits the wallet on every call.
- `safe_app.py` verifies the `monnify-signature` HMAC on the raw body, and uses a unique key in the database so a repeated event never credits twice.

`replay.py` plays the payment provider: it signs `sample_event.json` and delivers it as many times as you ask, or with a forged signature.

## Run it

```bash
pip install -r requirements.txt

python naive_app.py      # terminal 1, port 5000
python safe_app.py       # terminal 2, port 5001

python replay.py naive --times 3   # terminal 3
python replay.py safe --times 3
python replay.py safe --forge
python replay.py reset             # both wallets back to ₦0
```

Everything runs locally. No Monnify account or internet connection is needed.

## What you should see

```
$ python replay.py naive --times 3
delivery 1  -> 200  credited
delivery 2  -> 200  credited
delivery 3  -> 200  credited
wallet balance: ₦150,000.00

$ python replay.py safe --times 3
delivery 1  -> 200  credited
delivery 2  -> 200  duplicate, ignored
delivery 3  -> 200  duplicate, ignored
wallet balance: ₦50,000.00

$ python replay.py safe --forge
forged      -> 401  rejected
```

## Before you take this to production

The safe app covers two of the talk's three questions. The third is also essential in production:

- **Reply fast, confirm before giving value.** Do the work in a background job (Celery, RQ), then call Monnify's transaction status API and check both `paymentStatus == "PAID"` and that `amountPaid` matches what you expected before crediting anyone.
- Keep `MONNIFY_SECRET_KEY` in an environment variable. The demo falls back to a dummy key so it runs out of the box.
- Log every event you receive, including the ones you reject.

Monnify webhook docs: https://developers.monnify.com
