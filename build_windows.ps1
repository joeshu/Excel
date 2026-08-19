$ErrorActionPreference = "Stop"

Write-Host "Building frontend..."
Push-Location "$PSScriptRoot\frontend"
npm ci
npm run build
Pop-Location

$frontendDist = Join-Path $PSScriptRoot "frontend\dist"
$indexFile = Join-Path $frontendDist "index.html"
if (-not (Test-Path $indexFile)) {
  throw "frontend/dist/index.html was not generated"
}
$indexHtml = Get-Content -Raw $indexFile
$assetMatches = [regex]::Matches($indexHtml, 'src="(/app/assets/[^" ]+\.js)"')
if ($assetMatches.Count -eq 0) {
  throw "frontend/dist/index.html does not reference a /app/assets/*.js entrypoint"
}
foreach ($match in $assetMatches) {
  $assetRelativePath = $match.Groups[1].Value -replace '^/app/', '' -replace '/', '\\'
  if (-not (Test-Path (Join-Path $frontendDist $assetRelativePath))) {
    throw "Frontend entry asset is missing: $assetRelativePath"
  }
}

Write-Host "Installing Python dependencies..."
python -m pip install -r "$PSScriptRoot\backend\requirements.txt"
python -m pip install -r "$PSScriptRoot\packaging\requirements-build.txt"

Write-Host "Building Python sidecar..."
python -m PyInstaller --clean --noconfirm "$PSScriptRoot\packaging\ExcelWorkflow.spec"

Write-Host "Installing Electron dependencies..."
Push-Location $PSScriptRoot
npm ci
npm run dist
Pop-Location

$releaseDirectory = Join-Path $PSScriptRoot "release"
if (-not (Test-Path $releaseDirectory)) {
  throw "Electron build did not create the release directory"
}
$releaseArtifacts = Get-ChildItem -Path $releaseDirectory -File
if ($releaseArtifacts.Count -eq 0) {
  throw "Electron build did not create any release artifacts"
}
$legacyOutput = Join-Path $PSScriptRoot "ouput"
if (Test-Path $legacyOutput) {
  Write-Warning "Legacy ouput directory exists; distribute artifacts only from release\"
}
Write-Host "Created release\ExcelWorkflow installer and portable executable"
