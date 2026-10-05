@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Create the environment first: py -3.12 -m venv .venv
  echo Then install: .venv\Scripts\python.exe -m pip install -r backend\requirements.txt
  pause
  exit /b 1
)
.venv\Scripts\python.exe scripts\start.py
pause
