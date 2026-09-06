#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../.." && pwd)"

export BIOMAP_REPO="${BIOMAP_REPO:-${repo_root}}"
export BIOMAP_VIDEO_DIR="${BIOMAP_VIDEO_DIR:-${BIOMAP_REPO}/videos}"
export BIOMAP_DLC_ENV="${BIOMAP_DLC_ENV:-biomap-dlc}"
export BIOMAP_DLC_DEVICE="${BIOMAP_DLC_DEVICE:-cpu}"
export N8N_BLOCK_ENV_ACCESS_IN_NODE="false"
export NODES_EXCLUDE="[]"

if [[ ! -d "${BIOMAP_REPO}" ]]; then
    echo "BIOMAP_REPO does not exist: ${BIOMAP_REPO}" >&2
    exit 66
fi
cd -- "${BIOMAP_REPO}"

if ! command -v n8n >/dev/null 2>&1; then
    echo "n8n is not installed or is not on PATH. Install it with: npm install --global n8n" >&2
    exit 127
fi

exec n8n start
