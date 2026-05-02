import pytest

from core.composio_integration.composio_profile_service import ComposioProfileService


def _profile_row() -> dict:
    return {
        "profile_id": "profile-1",
        "account_id": "account-a",
        "mcp_qualified_name": "composio.gmail",
        "profile_name": "Gmail",
        "display_name": "Gmail",
        "encrypted_config": "not-a-valid-fernet-token",
        "config_hash": "bad",
        "is_active": True,
        "is_default": False,
    }


@pytest.mark.asyncio
async def test_unscoped_composio_recovery_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("COMPOSIO_ALLOW_UNSCOPED_PROFILE_RECOVERY", raising=False)
    service = ComposioProfileService(db_connection=object())
    called = False

    async def repair(row):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(service, "_repair_profile_row_without_decrypt", repair)

    row, config = await service._resolve_row_and_config(_profile_row())

    assert row["profile_id"] == "profile-1"
    assert config is None
    assert called is False


@pytest.mark.asyncio
async def test_unscoped_composio_recovery_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("COMPOSIO_ALLOW_UNSCOPED_PROFILE_RECOVERY", "true")
    service = ComposioProfileService(db_connection=object())
    called = False

    async def repair(row):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(service, "_repair_profile_row_without_decrypt", repair)

    _, config = await service._resolve_row_and_config(_profile_row())

    assert config is None
    assert called is True
