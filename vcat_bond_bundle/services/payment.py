from __future__ import annotations
import uuid
from datetime import datetime
import stripe
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..config import settings
from ..models import Case, Payment

def create_checkout_session(db: Session, case: Case) -> str:
    # Stub mode if keys not provided
    if not settings.STRIPE_PRICE_ID or not settings.STRIPE_SECRET_KEY:
        session_id = f"stub_{uuid.uuid4().hex}"
        checkout_url = f"https://example.com/checkout/{session_id}"
        payment = Payment(
            case_id=case.id,
            stripe_session_id=session_id,
            amount="39.00",
            currency="AUD",
            status="paid",
            created_at=datetime.utcnow(),
            paid_at=datetime.utcnow(),
        )
        db.add(payment)
        case.status = "paid"
        db.add(case)
        db.flush()
        return checkout_url

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
            mode="payment",
            success_url="https://example.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://example.com/cancel",
            metadata={"case_id": str(case.id)},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Stripe error: {exc}")

    payment = Payment(
        case_id=case.id,
        stripe_session_id=session.id,
        amount="39.00",
        currency="AUD",
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(payment)
    db.flush()
    return session.url

def handle_stripe_webhook(db: Session, payload: bytes, sig_header: str) -> None:
    if not settings.STRIPE_WEBHOOK_SECRET:
        return
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Webhook error: {exc}")

    if event["type"] != "checkout.session.completed":
        return
    session = event["data"]["object"]
    session_id = session["id"]

    payment = db.query(Payment).filter_by(stripe_session_id=session_id).first()
    if not payment:
        return
    payment.status = "paid"
    payment.paid_at = datetime.utcnow()
    db.add(payment)

    case = db.query(Case).filter_by(id=payment.case_id).first()
    if case:
        case.status = "paid"
        db.add(case)
    db.flush()
