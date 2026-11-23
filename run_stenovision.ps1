<#
.SYNOPSIS
    StenoVision Master Launcher (Backend API + Next.js Frontend + Observability)
.DESCRIPTION
    Launches the FastAPI Deep Learning inference microservice on http://localhost:8000
    with Prometheus metrics and HIPAA-safe structured logging, and the Next.js 15
    clinical workstation on http://localhost:3000.
.EXAMPLE
    .\run_stenovision.ps1
    .\run_stenovision.ps1 -BackendOnly
    .\run_stenovision.ps1 -FrontendOnly
#>

param (
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "     StenoVision - AI Coronary Stenosis Diagnostic Platform          " -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Ensure persistent logs directory exists
$LogDir = Join-Path $ScriptDir "backend\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "[+] Initialized persistent log directory: $LogDir" -ForegroundColor Gray
}

if (-not $FrontendOnly) {
    Write-Host "[1/2] Launching FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
    Write-Host "      - Metrics endpoint: http://localhost:8000/metrics" -ForegroundColor Gray
    Write-Host "      - Health endpoint:  http://localhost:8000/health" -ForegroundColor Gray
    Write-Host "      - HIPAA Log file:   $LogDir\stenovision.log" -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ScriptDir\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
}

if (-not $BackendOnly) {
    Write-Host "[2/2] Launching Next.js Clinical UI on http://localhost:3000..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ScriptDir\frontend'; npm run dev"
}

Write-Host "`n[Ready] System dispatched! Navigate to: http://localhost:3000 in your browser.`n" -ForegroundColor Cyan
