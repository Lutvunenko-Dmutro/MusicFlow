@echo off
echo ==============================================
echo Running Unit Tests for YouTube Music Pro
echo ==============================================

echo Installing test dependencies...
python -m pip install pytest pytest-mock

echo.
echo Running tests...
echo.

python -m pytest tests/ -v

echo.
echo ==============================================
echo Test run complete!
echo ==============================================
pause
