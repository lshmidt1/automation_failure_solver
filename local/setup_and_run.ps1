# Complete setup and run script
cd C:\Users\lshmidt\source\repos\automation_failure_solver\local

Write-Host "=== Setting up Jenkins Failure Analyzer ===" -ForegroundColor Cyan

# Activate venv
Write-Host "`n1. Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "`n2. Installing dependencies..." -ForegroundColor Yellow
pip install --quiet flask flask-cors boto3 requests

# Set AWS profile
Write-Host "`n3. Setting AWS profile..." -ForegroundColor Yellow
$env:AWS_PROFILE = "Claude-Code"

# Test AWS connection
Write-Host "`n4. Testing AWS connection..." -ForegroundColor Yellow
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "   ✅ AWS connected" -ForegroundColor Green
} catch {
    Write-Host "   ❌ AWS not connected" -ForegroundColor Red
    exit
}

# Start backend
Write-Host "`n5. Starting backend server..." -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to stop`n" -ForegroundColor Cyan

python app_bedrock_advanced.py
