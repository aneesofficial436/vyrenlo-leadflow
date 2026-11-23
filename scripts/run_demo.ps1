# End-to-end demo: submit public lead (requires seeded API key in $env:LEADFLOW_DEMO_API_KEY)
$ErrorActionPreference = "Stop"
$api = if ($env:LEADFLOW_API_URL) { $env:LEADFLOW_API_URL } else { "http://localhost:8000" }
$key = $env:LEADFLOW_DEMO_API_KEY
if (-not $key) {
    Write-Host "Set LEADFLOW_DEMO_API_KEY from seed_demo.py output" -ForegroundColor Yellow
    exit 1
}

$body = @{
    full_name = "Demo Prospect"
    email = "prospect.demo@example.com"
    enquiry_text = "Looking for 2-bed apartment, Marina, budget 18M PKR. Timeline 2 months."
    consent_channel_email = $true
} | ConvertTo-Json

Write-Host "Submitting public lead..."
$res = Invoke-RestMethod -Uri "$api/v1/public/leads" -Method Post -Headers @{
    "Content-Type" = "application/json"
    "X-Api-Key" = $key
} -Body $body
$res | ConvertTo-Json
Write-Host "Open dashboard leads and Mailpit http://localhost:8025"