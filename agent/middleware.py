"""Custom middleware: modify the system message at model-call time.

Uses wrap_model_call to intercept each LLM call and prepend/append context
(current date, tool hints) to the system message.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from langchain.agents.middleware import wrap_model_call
from langchain.agents.middleware.types import AgentMiddleware, AgentState, ModelRequest, ModelResponse
from langchain_core.messages import SystemMessage

from .configuration import Configuration

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def _prepend_to_system(existing: SystemMessage | None, text: str) -> SystemMessage:
    """Prepend *text* to an existing system message (or create one)."""
    if existing is None:
        return SystemMessage(content=text)
    content = existing.content
    if isinstance(content, str):
        return SystemMessage(content=text + "\n\n" + content)
    return SystemMessage(content=[{"type": "text", "text": text + "\n\n"}] + list(content))


def _append_to_system(existing: SystemMessage | None, text: str) -> SystemMessage:
    """Append *text* to an existing system message (or create one)."""
    if existing is None:
        return SystemMessage(content=text)
    content = existing.content
    if isinstance(content, str):
        return SystemMessage(content=content + "\n\n" + text)
    return SystemMessage(content=list(content) + [{"type": "text", "text": "\n\n" + text}])


# ---------------------------------------------------------------------------
# Current-date middleware (always on)
# ---------------------------------------------------------------------------


def build_current_date_middleware() -> AgentMiddleware[AgentState[Any], Any, Any]:
    """Prepend the current Pacific date/time to the system message on every model call."""

    @wrap_model_call
    async def _inject_date(request: ModelRequest, handler: Callable) -> ModelResponse:
        now = datetime.now(PACIFIC_TZ)
        date_str = now.strftime("Current date: %A, %B %d, %Y %H:%M %Z")
        new_system = _prepend_to_system(request.system_message, date_str)
        return await handler(request.override(system_message=new_system))

    return _inject_date


# ---------------------------------------------------------------------------
# Tool-hint middleware (conditional on config)
# ---------------------------------------------------------------------------


def get_system_prompt_additions(config: Configuration) -> str:
    """Return tool-specific hint text to append to the system message on each model call.

    Built from config.tool_prompt_hints (per-tool prompt_hint in blocks_to_config/mappings.yaml).
    """
    if not config.tool_prompt_hints:
        return ""
    return "\n\n".join(config.tool_prompt_hints.values())


def build_system_prompt_addition_middleware(addition: str) -> AgentMiddleware[AgentState[Any], Any, Any]:
    """Append *addition* to the system message on each model call."""
    if not addition.strip():

        @wrap_model_call
        async def _noop(request: ModelRequest, handler: Callable) -> ModelResponse:
            return await handler(request)

        return _noop

    text = addition.strip()

    @wrap_model_call
    async def _append_hints(request: ModelRequest, handler: Callable) -> ModelResponse:
        new_system = _append_to_system(request.system_message, text)
        return await handler(request.override(system_message=new_system))

    return _append_hints
