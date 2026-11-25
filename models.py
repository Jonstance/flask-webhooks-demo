"""Shared bits for both demo apps: a tiny wallet and a record of processed events."""
from decimal import Decimal

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Numeric(14, 2), nullable=False, default=0)


class ProcessedEvent(db.Model):
    # The primary key is the idempotency key: the database refuses a second row
    # with the same transactionReference, even if two retries arrive at once.
    reference = db.Column(db.String(64), primary_key=True)


def create_app(name: str, db_file: str) -> Flask:
    app = Flask(name)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_file}"
    db.init_app(app)

    with app.app_context():
        db.create_all()
        if db.session.get(Wallet, 1) is None:
            db.session.add(Wallet(id=1, balance=0))
            db.session.commit()

    @app.get("/balance")
    def balance():
        wallet = db.session.get(Wallet, 1)
        return jsonify(balance=str(wallet.balance))

    @app.post("/reset")  # demo only: put the wallet back to zero
    def reset():
        ProcessedEvent.query.delete()
        db.session.get(Wallet, 1).balance = 0
        db.session.commit()
        return jsonify(balance="0.00")

    return app


def add_to_wallet(amount) -> None:
    wallet = db.session.get(Wallet, 1)
    wallet.balance = Decimal(wallet.balance) + Decimal(str(amount))
