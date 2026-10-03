@echo off
setlocal
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
set "INSTALLER_NAME=python_installer.exe"

echo 🔍 Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is NOT installed in PATH.
    echo 📥 Downloading Python 3.11... Please wait.
    curl -L -o %INSTALLER_NAME% %PYTHON_URL%
    
    if %errorlevel% neq 0 (
        echo ❌ Failed to download Python. Please check your internet connection.
        pause
        exit /b
    )
    
    echo 🛠️ Installing Python silently (Adding to PATH)...
    start /wait %INSTALLER_NAME% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    if %errorlevel% neq 0 (
        echo ❌ Installation failed or was cancelled.
        pause
        exit /b
    )
    
    del %INSTALLER_NAME%
    echo ✅ Python installed successfully!
    echo ⚠️  Please RESTART this script (close and reopen RunMe.bat) to continue.
    pause
    exit /b
)

echo ✅ Python found. 
echo 📦 Installing required libraries (CustomTkinter, ReportLab)...
pip install -r requirements.txt

echo 🚀 Starting the Inventory App...
python main.py
pause
