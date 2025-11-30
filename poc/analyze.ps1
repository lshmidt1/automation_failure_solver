# Quick Analysis Script
param(
    [Parameter(Mandatory=$true)]
    [string]$XmlPath,
    
    [string]$RepoPath = ".",
    [string]$TestName = "Test Run",
    [string]$Output = "reports\analysis-$(Get-Date -Format 'yyyy-MM-dd-HHmmss').md"
)

Write-Host "🚀 Starting Analysis..." -ForegroundColor Cyan
Write-Host "   XML: $XmlPath" -ForegroundColor Yellow
Write-Host "   Repo: $RepoPath" -ForegroundColor Yellow
Write-Host "   Output: $Output" -ForegroundColor Yellow
Write-Host ""

python -m langgraph_poc.main `
    --xml-report $XmlPath `
    --repo-path $RepoPath `
    --test-name $TestName `
    --output $Output

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Analysis complete! Report saved to: $Output" -ForegroundColor Green
    
    # Ask if user wants to open the report
    $open = Read-Host "Open report? (y/n)"
    if ($open -eq 'y') {
        notepad $Output
    }
} else {
    Write-Host ""
    Write-Host "❌ Analysis failed!" -ForegroundColor Red
}