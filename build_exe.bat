@echo off
echo ==============================================
echo Building Music Flow (Fast VENV Method)
echo ==============================================

set SKIP_INSTALL=
if not exist "build_env\Scripts\activate.bat" (
    echo [1/3] Creating virtual environment - first time only, please wait...
    rmdir /S /Q build_env 2>nul
    python -m venv build_env
) else (
    echo [1/3] Using existing virtual environment - Fast mode...
    set SKIP_INSTALL=--skip-install
)

echo [2/3] Compiling safely inside the clean environment...
call build_env\Scripts\activate.bat
python scripts\build_with_progress.py %SKIP_INSTALL%

echo [3/3] Done!
call deactivate
pause
