"""Bridge between shared config and LangGraph.

Reads the agent config JSON written by config-api, builds a LangGraph agent,
and exports ``graph`` for ``langgraph dev``.

Falls back to a minimal stub agent when no config exists yet (first startup
before the user builds) or when the build fails.
"""

from __future__ import annotations

import asyncio
import os
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


async def _build():
    """Build a LangGraph agent from a resolved Configuration."""
    # initialize config
    config: Configuration = load(_CONFIG)

    # initialize model
    model = ChatOpenAI(
        model=config.model.name,
        base_url=config.model.url,
        api_key=config.model.api_key or "dummy",
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
        tools = await client.get_tools()

    # initialize middleware
    middleware = [build_current_date_middleware()]
    addition = get_system_prompt_additions(config)
    if addition:
        middleware.append(build_system_prompt_addition_middleware(addition))

    # initialize backend
    backend = LocalShellBackend(root_dir=os.getcwd(), virtual_mode=True, inherit_env=True)

    # initialize agent
    return create_deep_agent(
        model=model,
        tools=tools or None,
        system_prompt=config.system_prompt,
        middleware=tuple(middleware),
        backend=backend,
    )


graph = asyncio.run(_build())
