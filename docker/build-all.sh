#!/usr/bin/env bash
# Build all custom MCP tool server Docker images.
# Discovers folders automatically — each subfolder with a Dockerfile gets built as mcp/<name>.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for dir in "${SCRIPT_DIR}"/*/; do
    [ -f "${dir}/Dockerfile" ] || continue
    name="$(basename "${dir}")"
    tag="mcp/${name}"
    echo "=== Building ${tag} from ${name}/ ==="
    docker build -t "${tag}" "${dir}"
    echo ""
done

echo "All images built successfully."
docker images --filter "reference=mcp/*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
