#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip setuptools wheel
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
