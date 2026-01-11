#!/bin/bash
# Wrapper to run cypher-shell using credentials from .env

# Get the directory of this script
SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
  export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
else
  echo "Error: .env file not found at $PROJECT_ROOT/.env"
  exit 1
fi

# Check if cypher-shell is available
if ! command -v cypher-shell &> /dev/null; then
    echo "Error: cypher-shell is not in your PATH."
    echo "Please install it or ensure it is accessible."
    exit 1
fi

# Run cypher-shell with credentials
echo "Connecting to $NEO4J_URI as $NEO4J_USER..."
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" "$@"
