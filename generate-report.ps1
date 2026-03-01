<# 
.SYNOPSIS
    Generate test reports in various formats.

.DESCRIPTION
    Runs the test suite and generates reports in JUnit XML, HTML, or console formats.

.PARAMETER Format
    Output format: junit, html, console (default: console)

.PARAMETER OutputPath
    Path for report file (default: ./reports/)

.PARAMETER Skill
    Run tests for a specific skill only

.EXAMPLE
    .\generate-report.ps1
    # Runs tests with console output

.EXAMPLE
    .\generate-report.ps1 -Format junit -OutputPath ./results.xml
    # Generates JUnit XML report

.EXAMPLE
    .\generate-report.ps1 -Format html
    # Generates HTML report in ./reports/
#>

param(
    [ValidateSet('junit', 'html', 'console')]
    [string]$Format = 'console',
    
    [string]$OutputPath = '',
    
    [string]$Skill = ''
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$ReportsDir = Join-Path $ProjectRoot "reports"

# Get configuration info
function Get-TestConfig {
    $config = @{}
    $config.PythonVersion = (python --version 2>&1) -replace 'Python ', ''
    try {
        $config.CopilotVersion = (copilot --version 2>&1) -replace 'GitHub Copilot CLI ', ''
    } catch {
        $config.CopilotVersion = 'Not installed'
    }
    $config.SkillSource = if ($env:SKILL_SOURCE) { $env:SKILL_SOURCE } else { 'local' }
    $config.SkillDir = if ($env:SKILL_DIR) { $env:SKILL_DIR } else { 'C:\work\Problem-Based-SRS' }
    $config.Model = if ($env:COPILOT_MODEL) { $env:COPILOT_MODEL } else { 'gpt-5' }
    $config.PytestVersion = (python -c "import pytest; print(pytest.__version__)" 2>&1)
    return $config
}

$config = Get-TestConfig

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Generate Test Report" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Python:       $($config.PythonVersion)" -ForegroundColor Gray
Write-Host "  Copilot CLI:  $($config.CopilotVersion)" -ForegroundColor Gray
Write-Host "  Model:        $($config.Model)" -ForegroundColor Gray
Write-Host "  Skill Source: $($config.SkillSource)" -ForegroundColor Gray
Write-Host "  pytest:       $($config.PytestVersion)" -ForegroundColor Gray
Write-Host ""

# Ensure reports directory exists
if (-not (Test-Path $ReportsDir)) {
    New-Item -ItemType Directory -Path $ReportsDir | Out-Null
}

# Set default output paths
if (-not $OutputPath) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputPath = switch ($Format) {
        'junit' { Join-Path $ReportsDir "results_$timestamp.xml" }
        'html' { Join-Path $ReportsDir "report_$timestamp.html" }
        default { '' }
    }
}

# Build pytest arguments
$pytestArgs = @('tests/')

if ($Skill) {
    $testFile = "test_$($Skill -replace '-', '_').py"
    $pytestArgs = @("tests/$testFile")
}

switch ($Format) {
    'junit' {
        $pytestArgs += "--junitxml=$OutputPath"
        $pytestArgs += "-v"
        Write-Host "Output: $OutputPath" -ForegroundColor Yellow
    }
    'html' {
        # Check if pytest-html is installed
        $hasHtml = python -c "import pytest_html" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installing pytest-html..." -ForegroundColor Yellow
            python -m pip install pytest-html --quiet
        }
        $pytestArgs += "--html=$OutputPath"
        $pytestArgs += "--self-contained-html"
        $pytestArgs += "-v"
        Write-Host "Output: $OutputPath" -ForegroundColor Yellow
    }
    'console' {
        $pytestArgs += "-v"
        $pytestArgs += "--tb=short"
        $pytestArgs += "--durations=10"
    }
}

Write-Host "Format: $Format" -ForegroundColor Yellow
Write-Host ""

# Collect tests first to show count and list
Push-Location $ProjectRoot
$env:PYTHONPATH = "$ProjectRoot\scripts"

Write-Host "Collecting tests..." -ForegroundColor Gray
$collectCmd = "python -m pytest $($pytestArgs -join ' ') --collect-only -q"
$collectOutput = Invoke-Expression $collectCmd 2>&1
$testLines = $collectOutput | Where-Object { $_ -match '<Coroutine test_|::test_' }
$testCount = $testLines.Count

if ($testCount -gt 0) {
    Write-Host ""
    Write-Host "Tests to execute ($testCount total):" -ForegroundColor White
    $i = 1
    foreach ($test in $testLines) {
        $shortName = $test -replace '.*<Coroutine\s+', '' -replace '>.*', '' -replace '.*::', ''
        Write-Host "  [$i/$testCount] $shortName" -ForegroundColor Gray
        $i++
    }
    Write-Host ""
} else {
    Write-Host "No tests collected!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Run tests
try {
    $startTime = Get-Date
    $runCmd = "python -m pytest $($pytestArgs -join ' ')"
    Invoke-Expression $runCmd
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = $endTime - $startTime
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host "Timing:" -ForegroundColor White
Write-Host "  Started:  $($startTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
Write-Host "  Finished: $($endTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
Write-Host "  Duration: $($duration.ToString('mm\:ss\.fff'))" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

if ($OutputPath -and (Test-Path $OutputPath)) {
    Write-Host "Report saved: $OutputPath" -ForegroundColor Green
    
    # Open HTML report in browser
    if ($Format -eq 'html') {
        Write-Host "Opening report in browser..." -ForegroundColor Gray
        Start-Process $OutputPath
    }
}

if ($exitCode -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed" -ForegroundColor Red
}

exit $exitCode
