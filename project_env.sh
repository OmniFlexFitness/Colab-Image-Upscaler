#!/usr/bin/env bash
# project_env.sh - Minimal per-project environment bootstrap for OmniFlex Upscaler

# Guard against double sourcing
if [ -n "${UPSCALER_ENV_LOADED}" ]; then
  return 0 2>/dev/null || exit 0
fi
export UPSCALER_ENV_LOADED=1

# Resolve project root (directory containing this script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtualenv if present
if [ -d "${PROJECT_ROOT}/venv" ]; then
  # shellcheck source=/dev/null
  source "${PROJECT_ROOT}/venv/bin/activate"
else
  echo "[upscaler] No venv found. Create one with:"
  echo "          python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# Environment variables
export UPSCALER_CONFIG_PATH="${PROJECT_ROOT}/config.json"
export UPSCALER_IMPORT_PATH="${PROJECT_ROOT}/images/input"
export UPSCALER_EXPORT_PATH="${PROJECT_ROOT}/images/output"

# Ensure required directories exist
mkdir -p "${UPSCALER_IMPORT_PATH}" "${UPSCALER_EXPORT_PATH}"

# Aliases
alias upscaler="python \"${PROJECT_ROOT}/src/upscaler.py\""
alias upscaler-web="python \"${PROJECT_ROOT}/src/app.py\""

# Helper
upscaler-env-info () {
  echo "---- Upscaler Environment ----"
  echo "Project Root: ${PROJECT_ROOT}"
  echo "Venv:        ${VIRTUAL_ENV:-<none>}"
  echo "Config:      ${UPSCALER_CONFIG_PATH}"
  echo "Import Dir:  ${UPSCALER_IMPORT_PATH}"
  echo "Export Dir:  ${UPSCALER_EXPORT_PATH}"
  echo "Python:      $(command -v python 2>/dev/null || echo 'python not found')"
  echo "------------------------------"
}

echo "=========================================="
echo "OmniFlex Upscaler Environment Loaded"
echo "Aliases: upscaler | upscaler-web"
echo "Helper:  upscaler-env-info"
echo "=========================================="
