$ErrorActionPreference = "Stop"

Write-Host "Building frontend..."
Push-Location "$PSScriptRoot\frontend"
npm install
npm run build
Pop-Location

Write-Host "Installing Python dependencies..."
python -m pip install -r "$PSScriptRoot\backend\requirements.txt"
python -m pip install -r "$PSScriptRoot\packaging\requirements-build.txt"

Write-Host "Building executable..."
python -m PyInstaller --clean --noconfirm "$PSScriptRoot\packaging\ExcelWorkflow.spec"
Write-Host "Created dist\ExcelWorkflow.exe"
