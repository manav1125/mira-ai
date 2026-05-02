from decimal import Decimal

import pytest

from core.billing.external.stripe.handlers.checkout import CheckoutHandler


class StripeLikeSession(dict):
    def __getattr__(self, item):
        return self.get(item)


@pytest.mark.asyncio
async def test_credit_purchase_uses_payment_intent_as_credit_idempotency_key(monkeypatch):
    captured = {}

    async def fake_get_balances(account_id):
        return {"balance": 0, "expiring_credits": 0, "non_expiring_credits": 0}

    async def fake_update_purchase_by_payment_intent(**kwargs):
        captured["payment_update"] = kwargs

    async def fake_add_credits(**kwargs):
        captured["add_credits"] = kwargs
        return {"success": True}

    monkeypatch.setattr(
        "core.billing.external.stripe.handlers.checkout.billing_repo.get_credit_account_balances",
        fake_get_balances,
    )
    monkeypatch.setattr(
        "core.billing.external.stripe.handlers.checkout.billing_repo.update_purchase_by_payment_intent",
        fake_update_purchase_by_payment_intent,
    )
    monkeypatch.setattr(
        "core.billing.external.stripe.handlers.checkout.credit_manager.add_credits",
        fake_add_credits,
    )

    session = StripeLikeSession(
        id="cs_test_123",
        payment_intent="pi_test_123",
        metadata={"account_id": "acct_123", "credit_amount": "25"},
    )

    await CheckoutHandler._handle_credit_purchase(session, stripe_event_id="evt_123")

    assert captured["add_credits"]["account_id"] == "acct_123"
    assert captured["add_credits"]["amount"] == Decimal("25")
    assert captured["add_credits"]["is_expiring"] is False
    assert captured["add_credits"]["stripe_event_id"] == "credit_purchase:pi_test_123"
