# MousaviTax — one-shot knowledge index from Drive / official drop zone
# Run from repo root:  powershell -ExecutionPolicy Bypass -File scripts\win-index-knowledge.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "scripts\seed_knowledge.py"))) {
  $Root = (Get-Location).Path
}
Set-Location $Root
Write-Host "ROOT=$Root"

if (-not $env:VECTOR_DB_PATH) {
  $env:VECTOR_DB_PATH = Join-Path $Root "data\iran_tax_vectors.json"
}
if (-not $env:EMBEDDING_PROVIDER) {
  $env:EMBEDDING_PROVIDER = "fallback"
}
if (-not $env:GOOGLE_DRIVE_PRIMARY_FOLDER) {
  $env:GOOGLE_DRIVE_PRIMARY_FOLDER = "1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del"
}
if (-not $env:GOOGLE_DRIVE_FALLBACK_FOLDER) {
  $env:GOOGLE_DRIVE_FALLBACK_FOLDER = "1NcBkZOTemmVfnNKY7FgxuqbIXj6f4Dtl"
}

New-Item -ItemType Directory -Force -Path (Join-Path $Root "knowledge\official") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root "knowledge\drive_mirror") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root "data") | Out-Null

$py = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
  $py = ".\.venv\Scripts\python.exe"
}

Write-Host "EMBEDDING_PROVIDER=$env:EMBEDDING_PROVIDER"
Write-Host "VECTOR_DB_PATH=$env:VECTOR_DB_PATH"

if ($env:GOOGLE_SERVICE_ACCOUNT_JSON -and (Test-Path $env:GOOGLE_SERVICE_ACCOUNT_JSON)) {
  Write-Host "=== sync_drive_knowledge (Service Account) ==="
  & $py -m pip install -q google-api-python-client google-auth 2>$null
  & $py scripts\sync_drive_knowledge.py
} else {
  Write-Host "=== SKIP full Drive API sync (no GOOGLE_SERVICE_ACCOUNT_JSON) ==="
  Write-Host "Manual path: copy PDFs into knowledge\official\ then seed."
}

$manifest = Join-Path $Root "knowledge\drive_manifest.json"
if (Test-Path $manifest) {
  Write-Host "=== sync_drive_knowledge (manifest / gdown if configured) ==="
  & $py -m pip install -q gdown 2>$null
  & $py scripts\sync_drive_knowledge.py
}

Write-Host "=== seed_knowledge ==="
& $py scripts\seed_knowledge.py

Write-Host ""
Write-Host "DONE. Restart API with same VECTOR_DB_PATH, then:"
Write-Host "  Invoke-RestMethod http://127.0.0.1:8000/health"
