@echo off
setlocal
set "tool_dir=%~dp0"
set "venv_python=%tool_dir%.venv\Scripts\python.exe"

if not exist "%venv_python%" (
    where py >nul 2>&1
    if errorlevel 1 goto python_missing
    py -3.11 -c "import sys; assert sys.maxsize > 2**32" >nul 2>&1
    if errorlevel 1 goto python_missing
    echo [1/3] Creating the Python environment...
    py -3.11 -m venv "%tool_dir%.venv"
    if errorlevel 1 goto setup_failed
)

echo [2/3] Checking Python dependencies...
"%venv_python%" -m pip install --disable-pip-version-check -r "%tool_dir%requirements.txt"
if errorlevel 1 goto setup_failed

echo [3/3] Opening the column picker...
"%venv_python%" "%tool_dir%origin_plot_gui.py"
if errorlevel 1 goto run_failed
exit /b 0

:python_missing
echo Python 3.11 ^(64-bit^) was not found. Install it, then double-click this file again.
echo See README.md for the requirements.
goto failed

:setup_failed
echo Setup failed. Check the message above, then double-click this file to retry.
goto failed

:run_failed
echo The tool stopped with an error. Check the message above.

:failed
pause
exit /b 1
