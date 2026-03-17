"""Bridge between shared config and LangGraph.

Reads the agent config JSON written by config-api, builds a LangGraph agent,
and exports ``graph`` for ``langgraph dev``.

Falls back to a minimal stub agent when no config exists yet (first startup
before the user builds) or when the build fails.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import AsyncExitStack
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from .configuration import Configuration, load
from .middleware import (
    build_current_date_middleware,
    build_system_prompt_addition_middleware,
    get_system_prompt_additions,
)

_CONFIG = os.environ.get("AGENT_CONFIG_PATH", "./agent_config.yaml")

# Keeps MCP client connections alive for the lifetime of the process.
_exit_stack = AsyncExitStack()


async def _build():
    """Build a LangGraph agent from a resolved Configuration."""
    # initialize config
    config: Configuration = load(_CONFIG)

    if not config.model.api_key:
        raise RuntimeError(
            "Model API key is not set. "
            "Set the OPENROUTER_API_KEY environment variable or configure model.api_key in agent_config.yaml."
        )

    # initialize model
    model = ChatOpenAI(
        model=config.model.name,
        base_url=config.model.url,
        api_key=config.model.api_key,
        temperature=config.model.temperature,
        max_tokens=config.model.max_tokens,
        use_responses_api=False,
        **({"top_p": config.model.top_p} if config.model.top_p is not None else {}),
    )

    # initialize tools
    tools: list[Any] = []
    if config.mcp_servers:
        mcp_servers = {name: server.model_dump(exclude_none=True) for name, server in config.mcp_servers.items()}
        client = MultiServerMCPClient(mcp_servers)
        await _exit_stack.enter_async_context(client)
        tools = await client.get_tools()

    # initialize middleware
    middleware = [build_current_date_middleware()]
    addition = get_system_prompt_additions(config)
    if addition:
        middleware.append(build_system_prompt_addition_middleware(addition))

    # initialize backend
    backend = LocalShellBackend(root_dir=os.getcwd(), virtual_mode=True, inherit_env=False)

    # initialize agent
    return create_deep_agent(
        model=model,
        tools=tools or None,
        system_prompt=config.system_prompt,
        middleware=tuple(middleware),
        backend=backend,
    )


def _build_sync():
    """Build the agent, handling the case where an event loop is already running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import nest_asyncio

        nest_asyncio.apply()

    return asyncio.run(_build())


graph = _build_sync()
