@echo off
echo Starting Plexus API Development Server...
echo.

REM Change to project root directory (go up one level from server directory)
cd /d "%~dp0.."

REM Check if virtual environment exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using system Python.
)

REM Install dependencies if needed
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Test imports first
echo.
echo Testing imports...
python server\test_imports.py
if errorlevel 1 (
    echo.
    echo ❌ Import test failed. Please check the error messages above.
    pause
    exit /b 1
)

REM Start the development server
echo.
echo Starting API server...
python server\start.py

pause
