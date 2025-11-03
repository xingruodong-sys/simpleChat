#!/bin/sh
cd /app
streamlit run NaisPilot.py &
python3 -m src.task &
python3 main.py
