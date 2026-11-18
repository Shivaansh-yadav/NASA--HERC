#!/usr/bin/env bash
# Team Vansh HERC 2027: development environment setup
set -euo pipefail

echo "== Team Vansh HERC 2027 environment setup =="

if [ ! -d .venv ]; then
  python3 -m venv .venv
  echo "created virtualenv .venv"
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet numpy matplotlib
echo "python analysis dependencies installed (numpy, matplotlib)"

if python3 -c "import jupyter" 2>/dev/null; then
  echo "jupyter already available"
else
  pip install --quiet notebook jupyter-client ipykernel
  echo "jupyter installed for notebooks/analysis_walkthrough.ipynb"
fi

if command -v arduino-cli >/dev/null 2>&1; then
  echo "arduino-cli found: $(arduino-cli version)"
else
  echo "note: install arduino-cli to compile firmware/ (https://arduino.github.io/arduino-cli/)"
  echo "      then: arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 firmware"
fi

echo "done. try: make figures"
