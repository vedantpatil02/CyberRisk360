#!/bin/bash

echo "[+] Creating Python virtual environment..."

cd backend

python3 -m venv venv

source venv/bin/activate

echo "[+] Installing dependencies..."

pip install -r requirements.txt

echo "[+] Setup complete."
