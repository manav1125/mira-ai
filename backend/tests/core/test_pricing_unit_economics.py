from decimal import Decimal

from core.ai_models.models import ModelPricing
from core.billing.credits import calculator


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000000001"))


def test_calculate_usage_cost_breakdown_with_cache(monkeypatch):
    pricing = ModelPricing(
        input_cost_per_million_tokens=1.0,
        output_cost_per_million_tokens=5.0,
        cached_read_cost_per_million_tokens=0.1,
        cache_write_5m_cost_per_million_tokens=1.25,
        cache_write_1h_cost_per_million_tokens=2.0,
    )
    monkeypatch.setattr(calculator.model_manager, "get_pricing", lambda model: pricing)

    result = calculator.calculate_usage_cost_breakdown(
        prompt_tokens=1000,
        completion_tokens=200,
        model="test-model",
        cache_read_tokens=300,
        cache_creation_tokens=100,
    )

    assert result["non_cached_prompt_tokens"] == 600
    assert result["input_cost"] == Decimal("0.0006")
    assert result["output_cost"] == Decimal("0.001")
    assert money(result["cached_read_cost"]) == Decimal("0.000030000")
    assert money(result["cache_write_cost"]) == Decimal("0.000125000")
    assert money(result["actual_cost"]) == Decimal("0.001755000")
    assert money(result["billed_cost"]) == Decimal("0.003510000")
    assert result["markup_multiplier"] == Decimal("2.0")


def test_calculate_usage_cost_breakdown_falls_back_when_model_missing(monkeypatch):
    monkeypatch.setattr(calculator.model_manager, "get_pricing", lambda model: None)

    result = calculator.calculate_usage_cost_breakdown(
        prompt_tokens=500,
        completion_tokens=250,
        model="missing-model",
    )

    assert result["pricing_source"] == "fallback"
    assert result["prompt_tokens"] == 500
    assert result["completion_tokens"] == 250
    assert result["billed_cost"] == Decimal("0.01")
