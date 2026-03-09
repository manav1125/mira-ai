import asyncio

from core.config.official_worker_catalog import OFFICIAL_WORKER_KEYS
from core.services.supabase import DBConnection
from core.utils.logger import logger
from core.utils.official_worker_service import OfficialWorkerService


_installation_cache = set()
_installation_in_progress = set()


async def ensure_official_workers_installed(account_id: str) -> None:
    if account_id in _installation_cache:
        return

    if account_id in _installation_in_progress:
        return

    try:
        _installation_in_progress.add(account_id)
        db = DBConnection()
        client = await db.client

        existing = await client.table("agents").select("metadata").eq("account_id", account_id).execute()
        installed_keys = {
            (row.get("metadata") or {}).get("official_worker_key")
            for row in (existing.data or [])
            if (row.get("metadata") or {}).get("official_worker_key")
        }

        if OFFICIAL_WORKER_KEYS.issubset(installed_keys):
            _installation_cache.add(account_id)
            return

        logger.info(f"Installing missing official workers for account {account_id}")
        service = OfficialWorkerService(db)
        await service.install_for_user(account_id, replace_existing=False)
        _installation_cache.add(account_id)
    except Exception as exc:
        logger.error(f"Error ensuring official workers for {account_id}: {exc}")
    finally:
        _installation_in_progress.discard(account_id)


def trigger_official_workers_installation(account_id: str) -> None:
    try:
        asyncio.create_task(ensure_official_workers_installed(account_id))
    except RuntimeError:
        pass
