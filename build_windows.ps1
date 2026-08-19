$ErrorActionPreference = "Stop"

Write-Host "Building frontend..."
Push-Location "$PSScriptRoot\frontend"
npm install
npm run build
Pop-Location

Write-Host "Installing Python dependencies..."
python -m pip install -r "$PSScriptRoot\backend\requirements.txt"
python -m pip install -r "$PSScriptRoot\packaging\requirements-build.txt"

Write-Host "Building Python sidecar..."
python -m PyInstaller --clean --noconfirm "$PSScriptRoot\packaging\ExcelWorkflow.spec"

Write-Host "Installing Electron dependencies..."
Push-Location $PSScriptRoot
npm install
npm run dist
Pop-Location
Write-Host "Created release\ExcelWorkflow installer and portable executable"
