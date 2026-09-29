@echo off
cd /d "E:\Data Science Projects\CareTrack\app"
start "" python -m streamlit run app.py
timeout /t 3 >nul
start "" http://localhost:8501