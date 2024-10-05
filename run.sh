#!/bin/bash
uv venv .venv
uv pip install transformers tokenizers torch torchvision torchaudio torch-utils
uv pip install http://20.168.10.234:8080/wheel/syftbox-0.1.0-py3-none-any.whl
echo "installed packages"
uv run python main.py
