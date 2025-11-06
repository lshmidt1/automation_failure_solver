# Build Lambda deployment packages for Windows
$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot | Split-Path -Parent
$DIST = Join-Path $ROOT "dist"

# Clean and create dist folder
if (Test-Path $DIST) { Remove-Item -Recurse -Force $DIST }
New-Item -ItemType Directory -Force -Path $DIST | Out-Null

function Build-LambdaZip {
    param([string]$Name)
    
    Write-Host "Building $Name..." -ForegroundColor Green
    
    $src = Join-Path $ROOT "lambdas\$Name"
    $temp = Join-Path $env:TEMP ([System.IO.Path]::GetRandomFileName())
    
    # Create temp directory
    New-Item -ItemType Directory -Path $temp | Out-Null
    
    # Install requirements if they exist
    $reqFile = Join-Path $src "requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host "  Installing requirements..." -ForegroundColor Yellow
        pip install -r $reqFile -t $temp --quiet
    }
    
    # Copy Python files
    Write-Host "  Copying Python files..." -ForegroundColor Yellow
    Copy-Item "$src\*.py" $temp
    
    # Create zip
    $zipPath = Join-Path $DIST "$Name.zip"
    Write-Host "  Creating zip: $zipPath" -ForegroundColor Yellow
    Compress-Archive -Path "$temp\*" -DestinationPath $zipPath -Force
    
    # Cleanup
    Remove-Item -Recurse -Force $temp
    
    Write-Host "   Done: $Name`n" -ForegroundColor Green
}

# Build both lambdas
Build-LambdaZip "ingest_failure"
Build-LambdaZip "analyze_failure"

Write-Host "Zips created in $DIST" -ForegroundColor Cyan
Get-ChildItem $DIST | Format-Table Name, @{Label="Size (KB)"; Expression={[math]::Round($_.Length/1KB, 2)}}
