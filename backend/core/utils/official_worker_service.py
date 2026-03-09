from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.config.official_worker_catalog import OfficialWorkerSpec, get_official_worker_specs
from core.knowledge_base.file_processor import FileProcessor
from core.services.supabase import DBConnection
from core.utils.config import config
from core.utils.logger import logger


class OfficialWorkerService:
    """Install centrally managed specialist workers for user accounts."""

    def __init__(self, db: Optional[DBConnection] = None):
        self._db = db or DBConnection()
        self._file_processor = FileProcessor()

    async def install_for_user(self, account_id: str, replace_existing: bool = False) -> Dict[str, str]:
        client = await self._db.client
        existing_result = await client.table("agents").select("agent_id, metadata").eq("account_id", account_id).execute()
        existing_agents = existing_result.data or []

        existing_by_key = {}
        for agent in existing_agents:
            metadata = agent.get("metadata") or {}
            worker_key = metadata.get("official_worker_key")
            if worker_key:
                existing_by_key[worker_key] = agent

        installed: Dict[str, str] = {}

        for spec in get_official_worker_specs():
            existing_agent = existing_by_key.get(spec.key)
            if existing_agent and not replace_existing:
                agent_id = existing_agent["agent_id"]
                await self._sync_worker(
                    account_id=account_id,
                    agent_id=agent_id,
                    existing_metadata=existing_agent.get("metadata") or {},
                    spec=spec,
                )
                installed[spec.key] = agent_id
                continue

            if existing_agent and replace_existing:
                await self._delete_agent(existing_agent["agent_id"])

            agent_id = await self._create_worker(account_id, spec)
            installed[spec.key] = agent_id

        return installed

    async def install_for_all_users(self) -> Dict[str, int]:
        client = await self._db.client
        accounts_result = await client.schema("basejump").table("accounts").select("id").eq("personal_account", True).execute()
        account_ids = [row["id"] for row in (accounts_result.data or [])]

        installed_count = 0
        failed_count = 0

        for account_id in account_ids:
            try:
                result = await self.install_for_user(account_id, replace_existing=False)
                if result:
                    installed_count += 1
            except Exception as exc:
                failed_count += 1
                logger.error(f"Failed to install official workers for {account_id}: {exc}")

        return {
            "accounts_processed": len(account_ids),
            "installed_count": installed_count,
            "failed_count": failed_count,
        }

    async def _create_worker(self, account_id: str, spec: OfficialWorkerSpec) -> str:
        from core.agents import repo as agents_repo
        from core.versioning.version_service import get_version_service

        metadata = self._build_metadata(spec)

        agent = await agents_repo.create_agent(
            account_id=account_id,
            name=spec.name,
            description=spec.description,
            icon_name=spec.icon_name,
            icon_color=spec.icon_color,
            icon_background=spec.icon_background,
            is_default=False,
            metadata=metadata,
        )
        if not agent:
            raise RuntimeError(f"Failed to create official worker {spec.key}")

        version_service = await get_version_service()
        await version_service.create_version(
            agent_id=agent["agent_id"],
            user_id=account_id,
            system_prompt=spec.system_prompt,
            model=spec.model,
            configured_mcps=[],
            custom_mcps=[],
            agentpress_tools=spec.agentpress_tools,
            version_name="v1",
            change_description=f"Installed official worker {spec.name}",
        )

        if config.ENABLE_KNOWLEDGE_BASE and spec.knowledge_seeds:
            await self._ensure_knowledge_base(account_id, agent["agent_id"], spec)

        logger.info(f"Installed official worker {spec.key} for account {account_id}")
        return agent["agent_id"]

    async def _sync_worker(
        self,
        account_id: str,
        agent_id: str,
        existing_metadata: Dict[str, Any],
        spec: OfficialWorkerSpec,
    ) -> None:
        from core.agents import repo as agents_repo
        from core.versioning.version_service import get_version_service

        metadata = self._build_metadata(spec, existing_metadata)
        updates = {
            "name": spec.name,
            "description": spec.description,
            "icon_name": spec.icon_name,
            "icon_color": spec.icon_color,
            "icon_background": spec.icon_background,
            "metadata": metadata,
        }
        await agents_repo.update_agent(agent_id, account_id, updates)

        version_service = await get_version_service()
        current_version = await version_service.get_active_version(agent_id, account_id)

        current_prompt = current_version.system_prompt if current_version else ""
        current_model = current_version.model if current_version else None
        current_tools = current_version.agentpress_tools if current_version else {}
        prompt_changed = current_prompt != spec.system_prompt
        model_changed = current_model != spec.model
        tools_changed = current_tools != spec.agentpress_tools

        if prompt_changed or model_changed or tools_changed or current_version is None:
            await version_service.create_version(
                agent_id=agent_id,
                user_id=account_id,
                system_prompt=spec.system_prompt,
                model=spec.model,
                configured_mcps=current_version.configured_mcps if current_version else [],
                custom_mcps=current_version.custom_mcps if current_version else [],
                agentpress_tools=spec.agentpress_tools,
                change_description=f"Synced official worker {spec.name} with latest catalog",
            )

        if config.ENABLE_KNOWLEDGE_BASE and spec.knowledge_seeds:
            await self._ensure_knowledge_base(account_id, agent_id, spec)
        else:
            try:
                from core.cache.runtime_cache import invalidate_agent_config_cache

                await invalidate_agent_config_cache(agent_id)
            except Exception as exc:
                logger.warning(f"Failed to invalidate config cache for official worker {agent_id}: {exc}")

    def _build_metadata(
        self,
        spec: OfficialWorkerSpec,
        existing_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        metadata = dict(existing_metadata or {})
        now = datetime.now(timezone.utc).isoformat()
        metadata["official_worker_key"] = spec.key
        metadata["centrally_managed"] = True
        metadata["restrictions"] = spec.restrictions
        metadata["installation_date"] = metadata.get("installation_date") or now
        metadata["catalog_synced_at"] = now
        return metadata

    async def _ensure_knowledge_base(self, account_id: str, agent_id: str, spec: OfficialWorkerSpec) -> None:
        client = await self._db.client

        for seed in spec.knowledge_seeds:
            folder_id = await self._ensure_folder(account_id, seed.folder_name, seed.folder_description)
            entry_id = await self._ensure_entry(account_id, folder_id, seed.filename, seed.summary, seed.content, seed.mime_type)
            await self._ensure_assignment(account_id, agent_id, entry_id)

        try:
            from core.cache.runtime_cache import invalidate_agent_config_cache, invalidate_kb_context_cache

            await invalidate_agent_config_cache(agent_id)
            await invalidate_kb_context_cache(agent_id)
        except Exception as exc:
            logger.warning(f"Failed to invalidate KB caches for official worker {agent_id}: {exc}")

    async def _ensure_folder(self, account_id: str, name: str, description: str) -> str:
        client = await self._db.client
        existing = await client.table("knowledge_base_folders").select("folder_id").eq("account_id", account_id).eq("name", name).limit(1).execute()
        if existing.data:
            return existing.data[0]["folder_id"]

        result = await client.table("knowledge_base_folders").insert(
            {
                "account_id": account_id,
                "name": name,
                "description": description,
            }
        ).execute()
        if not result.data:
            raise RuntimeError(f"Failed to create knowledge base folder {name}")
        return result.data[0]["folder_id"]

    async def _ensure_entry(
        self,
        account_id: str,
        folder_id: str,
        filename: str,
        summary: str,
        content: str,
        mime_type: str,
    ) -> str:
        client = await self._db.client
        existing = await client.table("knowledge_base_entries").select("entry_id").eq("account_id", account_id).eq("folder_id", folder_id).eq("filename", filename).eq("is_active", True).limit(1).execute()
        if existing.data:
            return existing.data[0]["entry_id"]

        entry_id = str(uuid4())
        file_bytes = content.encode("utf-8")
        sanitized_filename = self._file_processor.sanitize_filename(filename)
        file_path = f"knowledge-base/{folder_id}/{entry_id}/{sanitized_filename}"

        await client.storage.from_("file-uploads").upload(file_path, file_bytes, {"content-type": mime_type})
        result = await client.table("knowledge_base_entries").insert(
            {
                "entry_id": entry_id,
                "folder_id": folder_id,
                "account_id": account_id,
                "filename": filename,
                "file_path": file_path,
                "file_size": len(file_bytes),
                "mime_type": mime_type,
                "summary": summary,
                "is_active": True,
            }
        ).execute()
        if not result.data:
            raise RuntimeError(f"Failed to create knowledge base entry {filename}")

        return entry_id

    async def _ensure_assignment(self, account_id: str, agent_id: str, entry_id: str) -> None:
        client = await self._db.client
        existing = await client.table("agent_knowledge_entry_assignments").select("assignment_id").eq("agent_id", agent_id).eq("entry_id", entry_id).limit(1).execute()
        if existing.data:
            return

        await client.table("agent_knowledge_entry_assignments").insert(
            {
                "agent_id": agent_id,
                "entry_id": entry_id,
                "account_id": account_id,
                "enabled": True,
            }
        ).execute()

    async def _delete_agent(self, agent_id: str) -> None:
        client = await self._db.client
        try:
            from core.triggers.trigger_service import get_trigger_service

            trigger_service = get_trigger_service(self._db)
            triggers_result = await client.table("agent_triggers").select("trigger_id").eq("agent_id", agent_id).execute()
            for trigger in triggers_result.data or []:
                await trigger_service.delete_trigger(trigger["trigger_id"])
        except Exception as exc:
            logger.warning(f"Failed to clean up triggers for official worker {agent_id}: {exc}")

        await client.table("agent_knowledge_entry_assignments").delete().eq("agent_id", agent_id).execute()
        await client.table("agents").delete().eq("agent_id", agent_id).execute()
