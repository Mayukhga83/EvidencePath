#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -f .venv/bin/python ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
if ! python -c 'import streamlit, sklearn, pandas, openai, pypdf, pydantic' >/dev/null 2>&1; then
  python -m pip install -r requirements.txt
fi
python -m streamlit run app.py
