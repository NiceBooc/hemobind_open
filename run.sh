#!/bin/bash

# HemoBind Universal Bootstrapper
# This script ensures a consistent environment across different Linux distributions.

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="$PROJECT_DIR/env"
BIN_DIR="$PROJECT_DIR/bin"
MAMBA_EXE="$BIN_DIR/micromamba"

echo "=== HemoBind Bootstrapper ==="

# 1. Ensure bin directory exists
mkdir -p "$BIN_DIR"

# 2. Download micromamba if missing
if [ ! -f "$MAMBA_EXE" ]; then
    echo "Downloading portable package manager (micromamba)..."
    ARCH=$(uname -m)
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    
    if [ "$ARCH" == "x86_64" ]; then ARCH="64"; fi
    
    curl -Ls https://micro.mamba.pm/api/micromamba/$OS-64/latest | tar -xvj -C "$BIN_DIR" bin/micromamba --strip-components=1
fi

# 3. Create or Update Environment
if [ ! -d "$ENV_DIR" ]; then
    echo "Creating isolated scientific environment (this may take a few minutes)..."
    "$MAMBA_EXE" create -y -p "$ENV_DIR" -f "$PROJECT_DIR/environment.yml"
else
    echo "Environment found. Checking for updates..."
    # Optional: uncomment to auto-update on every run
    # "$MAMBA_EXE" install -y -p "$ENV_DIR" -f "$PROJECT_DIR/environment.yml"
fi

# 4. Run HemoBind
echo "Launching HemoBind..."
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
# Ensure OpenMM can find system CUDA if available
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"

"$ENV_DIR/bin/python" -m hemobind_gui
