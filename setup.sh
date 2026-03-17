#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
echo "Installing dependencies (python: $PYTHON)..."
uv pip install --python "$PYTHON" "$SCRIPT_DIR" --quiet

echo "Building Docker images..."
bash "$SCRIPT_DIR/docker/build-all.sh" > /dev/null 2>&1

echo "Building chat UI..."
docker build -t deep-agents-ui "$SCRIPT_DIR/deep-agents-ui" > /dev/null 2>&1

echo "Starting chat UI..."
if docker ps -a --format '{{.Names}}' | grep -q '^deep-agents-ui$'; then
    docker start deep-agents-ui > /dev/null 2>&1
else
    docker run -d -p 3000:3000 --name deep-agents-ui --restart unless-stopped deep-agents-ui > /dev/null 2>&1
fi

echo "Done!"
