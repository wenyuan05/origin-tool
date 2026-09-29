@echo off
setlocal
set "tool_dir=%~dp0"
set "venv_python=%tool_dir%.venv\Scripts\python.exe"
set "python_tag="
set "check_python=import sys, struct, platform, tkinter, venv, ensurepip; assert sys.platform == 'win32' and platform.python_implementation() == 'CPython' and sys.version_info[:2] in ((3,8),(3,9),(3,10),(3,11),(3,12),(3,13),(3,14)) and struct.calcsize('P') == 8 and platform.machine().lower() in ('amd64', 'x86_64'); tkinter.Tcl()"

if exist "%venv_python%" goto existing_venv
if exist "%tool_dir%.venv\" goto venv_invalid

echo [1/3] Finding a compatible Python installation...
set "PYTHON_MANAGER_AUTOMATIC_INSTALL=0"
for /f "tokens=1" %%T in ('py --list-paths 2^>nul') do call :try_py %%T
if defined python_tag goto create_with_py
python -c "%check_python%" >nul 2>&1
if not errorlevel 1 goto create_with_python
python3 -c "%check_python%" >nul 2>&1
if not errorlevel 1 goto create_with_python3
goto python_missing

:create_with_py
echo Creating the environment with %python_tag%...
py %python_tag% -m venv "%tool_dir%.venv"
goto check_created

:create_with_python
echo Creating the environment with python from PATH...
python -m venv "%tool_dir%.venv"
goto check_created

:create_with_python3
echo Creating the environment with python3 from PATH...
python3 -m venv "%tool_dir%.venv"

:check_created
if errorlevel 1 goto setup_failed
if not exist "%venv_python%" goto setup_failed
goto install_dependencies

:existing_venv
"%venv_python%" -c "%check_python%" >nul 2>&1
if errorlevel 1 goto venv_invalid

:install_dependencies
echo [2/3] Checking Python dependencies...
"%venv_python%" -m pip install --disable-pip-version-check -r "%tool_dir%requirements.txt"
if errorlevel 1 goto setup_failed

echo [3/3] Opening the column picker...
"%venv_python%" "%tool_dir%app\group_plot_gui.py"
if errorlevel 1 goto run_failed
exit /b 0

:python_missing
echo No compatible 64-bit CPython ^(3.8 through 3.14^) was found.
echo See docs\PYTHON_INSTALL.md for step-by-step installation.
goto failed

:venv_invalid
echo The existing .venv cannot run this tool. Rename .venv in File Explorer,
echo then double-click this file again to create a new environment.
goto failed

:setup_failed
echo Setup failed. Check the message above, then double-click this file to retry.
goto failed

:run_failed
echo The tool stopped with an error. Check the message above.

:failed
pause
exit /b 1

:try_py
if defined python_tag exit /b 0
py %~1 -c "%check_python%" >nul 2>&1
if not errorlevel 1 set "python_tag=%~1"
exit /b 0
