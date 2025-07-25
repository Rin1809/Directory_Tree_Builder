#!/usr/bin/env bash

SCRIPT_DIR_RAW="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR_RAW}/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_NAME="moitruongao"
PYTHON_CMD="python3"

echo "==========================================================="
echo "Text Tree Builder Setup & Run Script for Linux/macOS"
echo "==========================================================="

if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo "ERROR: Python is not installed. Please install Python 3."
        exit 1
    fi
fi

if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment: $VENV_NAME..."
    "$PYTHON_CMD" -m venv "$VENV_NAME"
fi

echo "Activating virtual environment..."
source "$VENV_NAME/bin/activate"

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Running Text Tree Builder application..."
"$VENV_NAME/bin/python" run_app.py

deactivate
echo "==========================================================="