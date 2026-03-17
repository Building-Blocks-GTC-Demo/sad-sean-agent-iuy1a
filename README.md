# sad-sean-agent-iuy1a

An AI agent built with [LangGraph](https://github.com/langchain-ai/langgraph) and [deep-agents](https://github.com/langchain-ai/deep-agents), powered by Claude Sonnet 4.6 via OpenRouter. It comes with MCP-based tool servers for book search, web search, and Wikipedia lookups, plus a Next.js chat UI for interaction.

## Project Structure

```
.
├── agent/                    # Agent implementation
│   ├── agent.py              # Main agent builder & LangGraph graph
│   ├── configuration.py      # Pydantic config models & YAML loader
│   └── middleware.py          # Date injection & prompt hint middleware
├── deep-agents-ui/
│   └── Dockerfile            # Next.js chat UI (from langchain-ai/deep-agents-ui)
├── docker/                   # Dockerized MCP tool servers
│   ├── books/Dockerfile      # Open Library book search
│   ├── tavily/Dockerfile     # Tavily web search
│   └── build-all.sh          # Builds all MCP server images
├── agent_config.yaml         # Agent, model & MCP server configuration
├── langgraph.json            # LangGraph runtime entrypoint
├── pyproject.toml            # Python dependencies (3.12+)
├── env.example               # API key template
├── setup.sh                  # One-step install & build script
└── get-started.ipynb         # Guided setup notebook
```

## Quick Start

1. **Set up secrets** — copy `env.example` to `.env` and fill in your API keys:

   ```
   OPENROUTER_API_KEY=<your key>
   TAVILY_API_KEY=<your key>
   ```

2. **Run setup** — installs Python deps, builds Docker images for MCP servers, and starts the chat UI:

   ```bash
   bash setup.sh
   ```

3. **Start the agent**:

   ```bash
   langgraph dev --no-browser
   ```

4. **Open the chat UI** at `http://localhost:3000`, set the deployment URL to `http://localhost:2024` and assistant ID to `agent`.

If running on Brev, use the `get-started.ipynb` notebook for a guided walkthrough with secure link setup.

## Configuration

All agent behavior is driven by `agent_config.yaml`:

```yaml
model:
  api_key: $OPENROUTER_API_KEY
  name: anthropic/claude-sonnet-4.6
  temperature: 0.5
  url: https://openrouter.ai/api/v1

system_prompt: "You are a helpful assistant"

mcp_servers:
  books:
    command: docker
    args: [run, -i, --rm, mcp/books]
    transport: stdio
  tavily:
    command: docker
    args: [run, -i, --rm, -e, TAVILY_API_KEY=$TAVILY_API_KEY, mcp/tavily]
    transport: stdio
  wikipedia:
    command: uvx
    args: [wikipedia-mcp]
    transport: stdio

tool_prompt_hints: {}
```

- **model** — LLM provider, model name, temperature, and other generation params. Environment variables (prefixed with `$`) are resolved at load time.
- **system_prompt** — Base instructions for the agent.
- **mcp_servers** — Each entry defines an MCP tool server. Supports `stdio` and `sse` transports. Docker-based servers run in isolation; `uvx`-based servers run locally.
- **tool_prompt_hints** — Optional per-tool hints appended to the system prompt via middleware.

Override the config file path with the `AGENT_CONFIG_PATH` environment variable.

## MCP Tool Servers

| Server | Source | Transport | Description |
|--------|--------|-----------|-------------|
| **books** | [mcp-open-library](https://github.com/8enSmith/mcp-open-library) | stdio | Search and query the Open Library catalog |
| **tavily** | [tavily-mcp](https://www.npmjs.com/package/tavily-mcp) | stdio | Web search via the Tavily API |
| **wikipedia** | [wikipedia-mcp](https://pypi.org/project/wikipedia-mcp/) | stdio | Query Wikipedia articles |

To add a new tool server, add a Dockerfile under `docker/<name>/` and register it in `agent_config.yaml`. Run `docker/build-all.sh` to rebuild images.

## Architecture

The agent is assembled in `agent/agent.py`:

1. **Configuration** is loaded and validated via Pydantic models (`agent/configuration.py`).
2. **MCP tools** are connected through `langchain-mcp-adapters`, which translates MCP server capabilities into LangChain-compatible tools.
3. **Middleware** (`agent/middleware.py`) injects the current date/time (Pacific) and any tool prompt hints into the system message before each LLM call.
4. The resulting **LangGraph graph** is exported and served by `langgraph dev`.

## Development

```bash
# Install dependencies
uv pip install -e .

# Rebuild MCP Docker images after changes
bash docker/build-all.sh

# Start agent with hot-reload
langgraph dev --no-browser

# Tail agent logs
tail -f langgraph.log
```

## Learn More

- [Build an Agent Workshop](https://brev.nvidia.com/launchable/deploy?launchableID=env-32kC34ErT9wsqTcJyaKMxBEuhr2)
- [Brev Console](https://console.brev.dev)
