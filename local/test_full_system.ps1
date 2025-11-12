Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "     JENKINS FAILURE ANALYZER - FULL TEST SUITE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 1: Health
Write-Host "`n✓ Test 1: Health Check" -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:5000/health"
    Write-Host "  Status: $($health.status)" -ForegroundColor Yellow
    Write-Host "  Bedrock: $($health.bedrock)" -ForegroundColor Yellow
    Write-Host "  Version: $($health.version)" -ForegroundColor Yellow
} catch {
    Write-Host "  ✗ FAILED" -ForegroundColor Red
}

# Test 2: Real AI Analysis
Write-Host "`n✓ Test 2: Real Claude AI Analysis" -ForegroundColor Green
Write-Host "  (This takes 10-30 seconds...)" -ForegroundColor Yellow
try {
    $result = Invoke-RestMethod -Uri "http://localhost:5000/webhook?job=test-comprehensive&build=3001" -TimeoutSec 60
    Write-Host "  ✅ SUCCESS!" -ForegroundColor Green
    Write-Host "  Confidence: $($result.analysis.confidence)" -ForegroundColor Yellow
    Write-Host "  Root Cause Preview: $($result.analysis.root_cause.Substring(0, [Math]::Min(80, $result.analysis.root_cause.Length)))..." -ForegroundColor White
} catch {
    Write-Host "  ✗ FAILED: $_" -ForegroundColor Red
}

# Test 3: Results
Write-Host "`n✓ Test 3: Retrieve Results" -ForegroundColor Green
try {
    $results = Invoke-RestMethod -Uri "http://localhost:5000/results"
    Write-Host "  Total analyses: $($results.count)" -ForegroundColor Yellow
} catch {
    Write-Host "  ✗ FAILED" -ForegroundColor Red
}

# Test 4: Patterns
Write-Host "`n✓ Test 4: Pattern Detection" -ForegroundColor Green
try {
    $patterns = Invoke-RestMethod -Uri "http://localhost:5000/patterns"
    Write-Host "  Patterns detected: $($patterns.count)" -ForegroundColor Yellow
} catch {
    Write-Host "  ✗ FAILED" -ForegroundColor Red
}

# Test 5: Predictions
Write-Host "`n✓ Test 5: Failure Predictions" -ForegroundColor Green
try {
    $predictions = Invoke-RestMethod -Uri "http://localhost:5000/predictions"
    Write-Host "  Jobs analyzed: $($predictions.count)" -ForegroundColor Yellow
} catch {
    Write-Host "  ✗ FAILED" -ForegroundColor Red
}

# Test 6: Stats
Write-Host "`n✓ Test 6: Overall Stats" -ForegroundColor Green
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:5000/stats"
    Write-Host "  Total analyses: $($stats.total_analyses)" -ForegroundColor Yellow
    Write-Host "  Last 7 days: $($stats.last_7_days)" -ForegroundColor Yellow
} catch {
    Write-Host "  ✗ FAILED" -ForegroundColor Red
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "                    TESTS COMPLETE!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Check dashboard at http://localhost:3000" -ForegroundColor White
Write-Host "  2. Generate more test data" -ForegroundColor White
Write-Host "  3. Test with real Jenkins jobs" -ForegroundColor White
Write-Host ""
