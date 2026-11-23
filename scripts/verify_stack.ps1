# Quick smoke test for local LeadFlow stack
$ErrorActionPreference = "Stop"
$api = $env:LEADFLOW_API_URL
if (-not $api) { $api = "http://localhost:8000" }

Write-Host "Checking $api/health ..."
$h = Invoke-RestMethod -Uri "$api/health" -Method Get
if ($h.status -ne "ok") { throw "Health check failed" }

Write-Host "Checking $api/ready ..."
$r = Invoke-RestMethod -Uri "$api/ready" -Method Get
Write-Host "  database=$($r.database) redis=$($r.redis) status=$($r.status)"

$web = $env:LEADFLOW_WEB_URL
if (-not $web) { $web = "http://localhost:3000" }
try {
    $null = Invoke-WebRequest -Uri $web -Method Head -TimeoutSec 5
    Write-Host "Web OK: $web"
} catch {
    Write-Host "Web not reachable (optional): $web"
}

Write-Host "Stack verification complete."