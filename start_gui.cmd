@echo off
set "tool_dir=%~dp0"
if not exist "%tool_dir%.venv\Scripts\python.exe" (
    echo Python environment not found. See README.md for the one-time setup steps.
    pause
    exit /b 1
)
"%tool_dir%.venv\Scripts\python.exe" "%tool_dir%origin_plot_gui.py"
if errorlevel 1 pause
