<# 
.SYNOPSIS
    Run all tests: unit, e2e, coverage, and mutation tests.

.DESCRIPTION
    Master test runner that executes all test types and generates a unified summary.
    Runs pytest directly with proper filtering to avoid duplicate test execution.

.PARAMETER Unit
    Run unit tests only (excludes e2e tests)

.PARAMETER E2E
    Run e2e tests only (test_e2e_*.py files)

.PARAMETER Mutation
    Run mutation discovery only

.PARAMETER Coverage
    Run coverage analysis only

.PARAMETER Quick
    Run quick smoke tests only (3 key tests)

.PARAMETER Full
    Run full test suite including coverage and mutation (slow but thorough)

.PARAMETER Html
    Generate HTML reports for coverage

.PARAMETER Parallel
    Number of parallel workers for pytest tests

.PARAMETER FailFast
    Stop on first failure

.EXAMPLE
    .\run-all-tests.ps1
    # Runs ALL tests (unit + e2e) once

.EXAMPLE
    .\run-all-tests.ps1 -Full
    # Runs everything including coverage and mutation

.EXAMPLE
    .\run-all-tests.ps1 -Unit
    # Unit tests only (excludes e2e)

.EXAMPLE
    .\run-all-tests.ps1 -E2E
    # E2E tests only

.EXAMPLE
    .\run-all-tests.ps1 -Coverage -Html
    # Coverage analysis with HTML report
#>

param(
    [switch]$Unit,
    [switch]$E2E,
    [switch]$Mutation,
    [switch]$Coverage,
    [switch]$Quick,
    [switch]$Full,
    [switch]$Html,
    [int]$Parallel = 0,
    [switch]$FailFast,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$ReportsDir = Join-Path $ProjectRoot "reports"

# Ensure reports directory exists
if (-not (Test-Path $ReportsDir)) {
    New-Item -ItemType Directory -Path $ReportsDir | Out-Null
}

# Track results
$results = @{
    Unit = @{ Ran = $false; Passed = $false; Duration = $null; ExitCode = 0 }
    E2E = @{ Ran = $false; Passed = $false; Duration = $null; ExitCode = 0 }
    Coverage = @{ Ran = $false; Passed = $false; Duration = $null; ExitCode = 0 }
    Mutation = @{ Ran = $false; Passed = $false; Duration = $null; ExitCode = 0 }
}

$overallStartTime = Get-Date

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Problem-Based SRS - Complete Test Suite                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Determine what to run based on flags
# Default (no flags): run ALL tests
$runAllTests = -not $Unit -and -not $E2E -and -not $Mutation -and -not $Coverage -and -not $Quick -and -not $Full
$runUnit = $Unit -or $runAllTests
$runE2E = $E2E -or $runAllTests
$runCoverage = $Coverage -or $Full
$runMutation = $Mutation -or $Full
$runQuick = $Quick

# Quick mode overrides
if ($runQuick) {
    $runUnit = $false
    $runE2E = $false
    $runCoverage = $false
    $runMutation = $false
}

# Full mode includes everything
if ($Full) {
    $runUnit = $true
    $runE2E = $true
    $runCoverage = $true
    $runMutation = $true
}

# Show plan
Write-Host "Test Plan:" -ForegroundColor White
if ($runAllTests) {
    Write-Host "  All Tests:      ✓ Yes (running all tests once)" -ForegroundColor Green
} else {
    Write-Host "  Unit Tests:     $(if($runUnit){'✓ Yes (excluding e2e)'}else{'- Skip'})" -ForegroundColor $(if($runUnit){'Green'}else{'Gray'})
    Write-Host "  E2E Tests:      $(if($runE2E){'✓ Yes (test_e2e_*.py only)'}else{'- Skip'})" -ForegroundColor $(if($runE2E){'Green'}else{'Gray'})
}
if ($runQuick) {
    Write-Host "  Quick Mode:     ✓ Yes (3 smoke tests)" -ForegroundColor Green
}
Write-Host "  Coverage:       $(if($runCoverage){'✓ Yes'}else{'- Skip'})" -ForegroundColor $(if($runCoverage){'Green'}else{'Gray'})
Write-Host "  Mutation:       $(if($runMutation){'✓ Yes'}else{'- Skip'})" -ForegroundColor $(if($runMutation){'Green'}else{'Gray'})
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would execute the above test plan" -ForegroundColor Magenta
    exit 0
}

# Setup environment
$env:PYTHONPATH = "$ProjectRoot\scripts"
Push-Location $ProjectRoot

# Build pytest parallel args
$numWorkers = if ($Parallel -gt 0) { $Parallel } else { [Environment]::ProcessorCount }
$parallelArg = "-n $numWorkers"

try {
    # ============================================================================
    # Run Tests (ALL, Unit-only, E2E-only, or Quick)
    # ============================================================================
    if ($runAllTests -or $runUnit -or $runE2E -or $runQuick) {
        Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor White
        Write-Host "│  Running Tests                                                 │" -ForegroundColor White
        Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor White
        
        $testStart = Get-Date
        
        # Build test filter
        $testFilter = ""
        if ($runQuick) {
            # Quick: 3 key smoke tests
            $testFilter = "-k `"test_cp_generates_structured_notation or test_cn_generates_structured_notation or test_fr_uses_shall_notation`""
        } elseif ($runUnit -and -not $runE2E -and -not $runAllTests) {
            # Unit only: exclude e2e tests
            $testFilter = "--ignore=tests/test_e2e_crm.py --ignore=tests/test_e2e_microer.py"
        } elseif ($runE2E -and -not $runUnit -and -not $runAllTests) {
            # E2E only: only e2e tests
            $testFilter = "tests/test_e2e_crm.py tests/test_e2e_microer.py"
        }
        # else: runAllTests - no filter, run everything
        
        $failFastArg = if ($FailFast) { "-x" } else { "" }
        
        if ($testFilter -match "^tests/") {
            # Specific test files
            $pytestCmd = "python -m pytest $testFilter $parallelArg $failFastArg -v --tb=short"
        } else {
            # All tests with optional filter
            $pytestCmd = "python -m pytest tests/ $parallelArg $failFastArg -v --tb=short $testFilter"
        }
        
        Write-Host "Workers: $numWorkers" -ForegroundColor Gray
        Write-Host "Command: $pytestCmd" -ForegroundColor Gray
        Write-Host ""
        
        Invoke-Expression $pytestCmd
        $testExitCode = $LASTEXITCODE
        
        $testEnd = Get-Date
        $testDuration = $testEnd - $testStart
        
        if ($testExitCode -ne 0) {
            $results.Unit.Passed = $false
            if ($FailFast) {
                Write-Host "Tests failed. Stopping due to -FailFast." -ForegroundColor Red
                exit $testExitCode
            }
        } else {
            $results.Unit.Passed = $true
        }
        $results.Unit.Ran = $true
        $results.Unit.Duration = $testDuration
        $results.Unit.ExitCode = $testExitCode
    }

    # ============================================================================
    # Coverage Analysis
    # ============================================================================
    if ($runCoverage) {
        Write-Host ""
        Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor White
        Write-Host "│  Coverage Analysis                                             │" -ForegroundColor White
        Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor White
        
        $coverageStart = Get-Date
        $results.Coverage.Ran = $true
        
        $coverageCmd = ".\run-mutation-tests.ps1 -Coverage -Parallel $numWorkers"
        if ($Html) {
            $coverageCmd += " -Html"
        }
        
        Invoke-Expression $coverageCmd
        $results.Coverage.ExitCode = $LASTEXITCODE
        
        $coverageEnd = Get-Date
        $results.Coverage.Duration = $coverageEnd - $coverageStart
        $results.Coverage.Passed = ($results.Coverage.ExitCode -eq 0)
    }

    # ============================================================================
    # Mutation Tests
    # ============================================================================
    if ($runMutation) {
        Write-Host ""
        Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor White
        Write-Host "│  Mutation Discovery                                            │" -ForegroundColor White
        Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor White
        
        $mutationStart = Get-Date
        $results.Mutation.Ran = $true
        
        $mutationCmd = ".\run-mutation-tests.ps1 -Mutation"
        
        Invoke-Expression $mutationCmd
        $results.Mutation.ExitCode = $LASTEXITCODE
        
        $mutationEnd = Get-Date
        $results.Mutation.Duration = $mutationEnd - $mutationStart
        $results.Mutation.Passed = $true  # Discovery always "passes"
    }

} finally {
    Pop-Location
}

# ============================================================================
# Summary
# ============================================================================
$overallEndTime = Get-Date
$totalDuration = $overallEndTime - $overallStartTime

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                      TEST SUMMARY                              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true
$anyFailed = $false

foreach ($testType in @('Unit', 'E2E', 'Coverage', 'Mutation')) {
    $r = $results[$testType]
    if ($r.Ran) {
        $statusIcon = if ($r.Passed) { "✓" } else { "✗" }
        $statusColor = if ($r.Passed) { "Green" } else { "Red" }
        $duration = if ($r.Duration) { $r.Duration.ToString('mm\:ss') } else { "N/A" }
        
        Write-Host "  $statusIcon " -NoNewline -ForegroundColor $statusColor
        Write-Host "$($testType.PadRight(12))" -NoNewline -ForegroundColor White
        Write-Host " $duration" -ForegroundColor Gray
        
        if (-not $r.Passed) {
            $allPassed = $false
            $anyFailed = $true
        }
    } else {
        Write-Host "  - $($testType.PadRight(12)) Skipped" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "────────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host "  Total Duration: $($totalDuration.ToString('mm\:ss\.fff'))" -ForegroundColor Yellow
Write-Host ""

# Generate JSON summary report
$summaryReport = @{
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    duration_seconds = $totalDuration.TotalSeconds
    results = @{}
    overall_passed = $allPassed
}

foreach ($testType in @('Unit', 'E2E', 'Coverage', 'Mutation')) {
    $r = $results[$testType]
    if ($r.Ran) {
        $summaryReport.results[$testType.ToLower()] = @{
            ran = $r.Ran
            passed = $r.Passed
            exit_code = $r.ExitCode
            duration_seconds = if ($r.Duration) { $r.Duration.TotalSeconds } else { 0 }
        }
    }
}

$summaryJson = $summaryReport | ConvertTo-Json -Depth 3
$summaryPath = Join-Path $ReportsDir "test-summary.json"
$summaryJson | Out-File -FilePath $summaryPath -Encoding UTF8

Write-Host "Summary saved: $summaryPath" -ForegroundColor Gray
Write-Host ""

if ($allPassed) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗ Some tests failed. Check output above for details." -ForegroundColor Red
    
    # Show which tests to re-run
    Write-Host ""
    Write-Host "To re-run failed tests:" -ForegroundColor Yellow
    if ($results.Unit.Ran -and -not $results.Unit.Passed) {
        Write-Host "  .\run-unit-tests.ps1" -ForegroundColor Gray
    }
    if ($results.E2E.Ran -and -not $results.E2E.Passed) {
        Write-Host "  .\run-e2e-tests.ps1" -ForegroundColor Gray
    }
    
    exit 1
}
