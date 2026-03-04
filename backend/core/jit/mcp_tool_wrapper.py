import asyncio
import json
from typing import Dict, Any
from core.utils.logger import logger


class MCPToolExecutor:

    def __init__(self, mcp_config: Dict[str, Any], account_id: str = None):
        self.mcp_config = mcp_config
        self.account_id = account_id
        custom_type = mcp_config.get("customType", mcp_config.get("type", "standard"))
        self.server_type = custom_type

        self.tool_info = {
            'custom_type': custom_type,
            'custom_config': mcp_config.get('config', {}),
            'original_name': None
        }
    
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        try:
            self.tool_info['original_name'] = tool_name
            
            if self.server_type == "composio":
                return await self._execute_composio_tool(tool_name, args)
            elif self.server_type == "sse":
                return await self._execute_sse_tool(tool_name, args)
            elif self.server_type == "http":
                return await self._execute_http_tool(tool_name, args)
            elif self.server_type == "json":
                return await self._execute_json_tool(tool_name, args)
            else:
                return await self._execute_http_tool(tool_name, args)
                
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] Failed to execute {tool_name}: {e}")
            raise
    
    async def _execute_composio_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        def _format_exception(exc: Exception) -> str:
            messages = []

            def _walk(current: Exception) -> None:
                nested = getattr(current, 'exceptions', None)
                if nested:
                    for child in nested:
                        _walk(child)
                    return
                messages.append(f"{type(current).__name__}: {current}")

            _walk(exc)
            if messages:
                return " | ".join(dict.fromkeys(messages))
            return f"{type(exc).__name__}: {exc}"

        from core.composio_integration.composio_profile_service import ComposioProfileService
        from core.composio_integration.connected_account_service import ConnectedAccountService
        from core.services.supabase import DBConnection
        from mcp.client.streamable_http import streamablehttp_client
        from mcp import ClientSession
        from core.agentpress.tool import ToolResult

        custom_config = self.tool_info['custom_config']
        preferred_profile_id = custom_config.get('profile_id')
        if not self.account_id:
            raise ValueError(f"Missing account_id for Composio tool '{tool_name}' execution")

        toolkit_slug = custom_config.get('toolkit_slug') or self.mcp_config.get('toolkit_slug')
        if not toolkit_slug:
            mcp_qualified_name = self.mcp_config.get('mcp_qualified_name', '')
            if isinstance(mcp_qualified_name, str) and mcp_qualified_name.startswith('composio.'):
                toolkit_slug = mcp_qualified_name.split('.', 1)[1]
        if not toolkit_slug and '_' in tool_name:
            toolkit_slug = tool_name.split('_', 1)[0].lower()
        if not toolkit_slug:
            raise ValueError(f"Unable to determine toolkit_slug for Composio tool '{tool_name}'")

        try:
            db = DBConnection()
            profile_service = ComposioProfileService(db)
            candidates = await profile_service.get_runtime_profile_candidates(
                account_id=self.account_id,
                toolkit_slug=toolkit_slug,
                preferred_profile_id=preferred_profile_id
            )
            candidate_errors = []
            for resolved_profile_id, mcp_url in candidates:
                refresh_attempted = False
                attempted_urls = [mcp_url]

                while attempted_urls:
                    runtime_url = attempted_urls.pop(0)
                    try:
                        profile_config = await profile_service.get_profile_config(
                            resolved_profile_id,
                            account_id=self.account_id
                        )
                        runtime_user_id = profile_config.get("user_id")
                        runtime_connected_account_id = profile_config.get("connected_account_id")
                        connected_account_user_id = None

                        if runtime_connected_account_id:
                            try:
                                connected_account_service = ConnectedAccountService()
                                connected_account = await connected_account_service.get_connected_account(
                                    runtime_connected_account_id
                                )
                                if connected_account and getattr(connected_account, "user_id", None):
                                    connected_account_user_id = connected_account.user_id
                            except Exception as connected_account_error:
                                logger.warning(
                                    f"⚠️ [MCP EXEC] Could not fetch connected account user id for "
                                    f"{runtime_connected_account_id}: {connected_account_error}"
                                )

                        arg_variants = []
                        base_args = dict(args or {})
                        arg_variants.append(base_args)

                        candidate_user_ids = []
                        for user_id_candidate in [connected_account_user_id, runtime_user_id]:
                            if user_id_candidate and user_id_candidate not in candidate_user_ids:
                                candidate_user_ids.append(user_id_candidate)

                        if isinstance(base_args, dict):
                            if 'user_id' in base_args:
                                for user_id_candidate in candidate_user_ids:
                                    if base_args.get('user_id') == user_id_candidate:
                                        continue
                                    aligned_args = dict(base_args)
                                    aligned_args['user_id'] = user_id_candidate
                                    arg_variants.append(aligned_args)

                                if str(base_args.get('user_id')).strip().lower() == 'me':
                                    removed_user_id_args = dict(base_args)
                                    removed_user_id_args.pop('user_id', None)
                                    arg_variants.append(removed_user_id_args)
                            else:
                                for user_id_candidate in candidate_user_ids:
                                    with_user_id_args = dict(base_args)
                                    with_user_id_args['user_id'] = user_id_candidate
                                    arg_variants.append(with_user_id_args)

                        deduped_variants = []
                        seen_signatures = set()
                        for variant in arg_variants:
                            try:
                                signature = json.dumps(variant or {}, sort_keys=True, default=str)
                            except Exception:
                                signature = repr(variant)
                            if signature in seen_signatures:
                                continue
                            seen_signatures.add(signature)
                            deduped_variants.append(variant)

                        logger.debug(
                            f"⚡ [MCP EXEC] Trying Composio profile {resolved_profile_id} for {tool_name}"
                        )
                        async with streamablehttp_client(runtime_url) as (read, write, _):
                            async with ClientSession(read, write) as session:
                                await session.initialize()

                                last_variant_error = None
                                mismatch_text = "connected account user id does not match the provided user id"
                                for variant_index, variant in enumerate(deduped_variants):
                                    is_last_variant = variant_index == len(deduped_variants) - 1
                                    try:
                                        result = await session.call_tool(tool_name, arguments=variant)
                                        content = self._extract_result_content(result)
                                        output_text = str(content)

                                        # Some MCP servers return user-id mismatch as successful text output
                                        # instead of raising exceptions. Treat it as retryable failure.
                                        if mismatch_text in output_text.lower():
                                            mismatch_error = ValueError(output_text)
                                            last_variant_error = mismatch_error
                                            if not is_last_variant:
                                                logger.warning(
                                                    f"⚠️ [MCP EXEC] User-id mismatch output for {tool_name}; "
                                                    f"trying aligned args variant"
                                                )
                                                continue
                                            raise mismatch_error

                                        if resolved_profile_id != preferred_profile_id:
                                            logger.info(
                                                f"⚡ [MCP EXEC] Fallback Composio profile resolved for {tool_name}: "
                                                f"{preferred_profile_id} -> {resolved_profile_id}"
                                            )
                                            custom_config['profile_id'] = resolved_profile_id

                                        if variant != base_args:
                                            logger.info(
                                                f"⚡ [MCP EXEC] Applied argument alignment retry for {tool_name} "
                                                f"(profile {resolved_profile_id})"
                                            )

                                        return ToolResult(success=True, output=str(content))
                                    except Exception as variant_error:
                                        formatted_variant_error = _format_exception(variant_error)
                                        last_variant_error = variant_error

                                        if (
                                            mismatch_text in formatted_variant_error.lower()
                                            and not is_last_variant
                                        ):
                                            logger.warning(
                                                f"⚠️ [MCP EXEC] User-id mismatch for {tool_name}; trying aligned args variant"
                                            )
                                            continue

                                        if not is_last_variant:
                                            continue

                                if last_variant_error:
                                    raise last_variant_error
                    except Exception as candidate_error:
                        formatted_error = _format_exception(candidate_error)
                        if not refresh_attempted:
                            refresh_attempted = True
                            refreshed_url = await profile_service.refresh_runtime_mcp_url(
                                profile_id=resolved_profile_id,
                                account_id=self.account_id,
                                toolkit_slug=toolkit_slug
                            )
                            if refreshed_url and refreshed_url != runtime_url:
                                logger.info(
                                    f"⚡ [MCP EXEC] Retrying {tool_name} with refreshed MCP URL (profile {resolved_profile_id})"
                                )
                                attempted_urls.append(refreshed_url)
                                continue
                        candidate_errors.append(
                            f"profile_id={resolved_profile_id}: {formatted_error}"
                        )
                        logger.warning(
                            f"⚠️ [MCP EXEC] Composio execution failed for {tool_name} with profile {resolved_profile_id}: {formatted_error}"
                        )
                        break

            raise ValueError(
                f"Failed to execute Composio tool '{tool_name}' after trying {len(candidates)} profile(s). "
                f"Errors: {' | '.join(candidate_errors)}"
            )
            
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] Composio execution failed for {tool_name}: {e}")
            from core.agentpress.tool import ToolResult
            return ToolResult(
                success=False,
                output=f"Failed to execute Composio tool: {str(e)}"
            )
    
    async def _execute_sse_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        from mcp.client.sse import sse_client
        from mcp import ClientSession
        from core.agentpress.tool import ToolResult
        
        custom_config = self.tool_info['custom_config']
        url = custom_config.get('url')
        
        if not url:
            return ToolResult(
                success=False,
                output="Missing 'url' in SSE MCP config"
            )
        
        headers = custom_config.get('headers', {})
        
        try:
            async with asyncio.timeout(30):
                try:
                    async with sse_client(url, headers=headers) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(tool_name, arguments=args)
                            content = self._extract_result_content(result)
                            logger.debug(f"⚡ [MCP EXEC] Executed {tool_name} via SSE")
                            return ToolResult(success=True, output=str(content))
                except TypeError as e:
                    if "unexpected keyword argument" in str(e):
                        async with sse_client(url) as (read, write):
                            async with ClientSession(read, write) as session:
                                await session.initialize()
                                result = await session.call_tool(tool_name, arguments=args)
                                content = self._extract_result_content(result)
                                logger.debug(f"⚡ [MCP EXEC] Executed {tool_name} via SSE (no headers)")
                                return ToolResult(success=True, output=str(content))
                    else:
                        raise
        except asyncio.TimeoutError:
            logger.error(f"❌ [MCP EXEC] SSE execution timeout for {tool_name}")
            return ToolResult(
                success=False,
                output=f"SSE tool execution timeout after 30 seconds"
            )
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] SSE execution failed for {tool_name}: {e}")
            return ToolResult(
                success=False,
                output=f"Failed to execute SSE tool: {str(e)}"
            )
    
    async def _execute_http_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        from mcp.client.streamable_http import streamablehttp_client
        from mcp import ClientSession
        from core.agentpress.tool import ToolResult
        
        custom_config = self.tool_info['custom_config']
        url = custom_config.get('url')
        
        if not url:
            return ToolResult(
                success=False,
                output="Missing 'url' in HTTP MCP config"
            )
        
        try:
            async with asyncio.timeout(30):
                async with streamablehttp_client(url) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=args)
                        content = self._extract_result_content(result)
                        logger.debug(f"⚡ [MCP EXEC] Executed {tool_name} via HTTP")
                        return ToolResult(success=True, output=str(content))
        except asyncio.TimeoutError:
            logger.error(f"❌ [MCP EXEC] HTTP execution timeout for {tool_name}")
            return ToolResult(
                success=False,
                output=f"HTTP tool execution timeout after 30 seconds"
            )
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] HTTP execution failed for {tool_name}: {e}")
            return ToolResult(
                success=False,
                output=f"Failed to execute HTTP tool: {str(e)}"
            )
    
    async def _execute_json_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from core.agentpress.tool import ToolResult
        
        custom_config = self.tool_info['custom_config']
        command = custom_config.get('command')
        
        if not command:
            return ToolResult(
                success=False,
                output="Missing 'command' in JSON/stdio MCP config"
            )
        
        try:
            server_params = StdioServerParameters(
                command=command,
                args=custom_config.get("args", []),
                env=custom_config.get("env", {})
            )
            
            async with asyncio.timeout(30):
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=args)
                        content = self._extract_result_content(result)
                        logger.debug(f"⚡ [MCP EXEC] Executed {tool_name} via JSON/stdio")
                        return ToolResult(success=True, output=str(content))
        except asyncio.TimeoutError:
            logger.error(f"❌ [MCP EXEC] JSON/stdio execution timeout for {tool_name}")
            return ToolResult(
                success=False,
                output=f"JSON/stdio tool execution timeout after 30 seconds"
            )
        except Exception as e:
            logger.error(f"❌ [MCP EXEC] JSON/stdio execution failed for {tool_name}: {e}")
            return ToolResult(
                success=False,
                output=f"Failed to execute JSON/stdio tool: {str(e)}"
            )
    
    def _extract_result_content(self, result: Any) -> str:
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if hasattr(item, 'text'):
                        text_parts.append(item.text)
                    else:
                        text_parts.append(str(item))
                return "\n".join(text_parts)
            elif hasattr(content, 'text'):
                return content.text
            else:
                return str(content)
        elif isinstance(result, dict):
            return result.get('content', str(result))
        else:
            return str(result)
