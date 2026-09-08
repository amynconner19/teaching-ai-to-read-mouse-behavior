#!/usr/bin/env bash
#
# Launcher for self-hosted n8n with the BIOMAP DeepLabCut variables set.
#
# This script is NOT a dependency installer. It does:
#   - derive or preserve BIOMAP_REPO and BIOMAP_VIDEO_DIR
#   - set or preserve BIOMAP_DLC_ENV and BIOMAP_DLC_DEVICE
#   - configure n8n environment access for the Execute Command node
#   - start the local n8n server with the repository as working directory
#
# It does NOT install Git, Git LFS, Miniforge/Conda, Node.js, n8n, DeepLabCut,
# or PyTorch, and it never creates the biomap-dlc environment or materializes
# Git LFS model files. Install those first; see n8n/docs/BIOMAP_N8N_SETUP.md.
#
# Values already exported in the calling shell take precedence.

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
