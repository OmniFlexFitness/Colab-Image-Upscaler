#!/usr/bin/env bash
set -e
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
[ -f requirements.txt ] && pip install -r requirements.txt
echo "Venv ready."
