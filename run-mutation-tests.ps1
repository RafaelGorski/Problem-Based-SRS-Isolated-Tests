<# 
.SYNOPSIS
    Run mutation tests and coverage analysis.

.DESCRIPTION
    Executes mutmut mutation testing (via WSL) and coverage analysis on scripts/.
    Default behavior runs full e2e: coverage + mutation + HTML reports.

.PARAMETER Coverage
    Run coverage analysis only

.PARAMETER Mutation
    Run mutation testing only

.PARAMETER Quick
    Run quick mutation test on a single file (fixtures.py)

.PARAMETER File
    Target a specific file for mutation testing

.PARAMETER ShowSurvivors
    Display details of surviving mutants

.PARAMETER Html
    Generate HTML reports (included by default)

.PARAMETER NoHtml
    Skip HTML report generation

.PARAMETER Parallel
    Number of parallel workers for pytest (default: auto-detect CPU cores)

.PARAMETER Sequential
    Run tests sequentially (no parallelism)

.EXAMPLE
    .\run-mutation-tests.ps1
    # Runs full e2e: coverage + mutation + HTML reports

.EXAMPLE
    .\run-mutation-tests.ps1 -Coverage
    # Runs coverage analysis only with HTML

.EXAMPLE
    .\run-mutation-tests.ps1 -Mutation -Quick
    # Quick mutation test on fixtures.py

.EXAMPLE
    .\run-mutation-tests.ps1 -ShowSurvivors
    # Shows details of surviving mutants
#>

param(
    [switch]$Coverage,
    [switch]$Mutation,
    [switch]$Quick,
    [string]$File = '',
    [switch]$ShowSurvivors,
    [switch]$Html,
    [switch]$NoHtml,
    [int]$Parallel = 0,
    [switch]$Sequential,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$ReportsDir = Join-Path $ProjectRoot "reports"

# Determine parallel workers
$numWorkers = if ($Sequential) { 0 } elseif ($Parallel -gt 0) { $Parallel } else { [Environment]::ProcessorCount }

# Default: HTML is on unless -NoHtml specified
$generateHtml = -not $NoHtml

# Ensure reports directory exists
if (-not (Test-Path $ReportsDir)) {
    New-Item -ItemType Directory -Path $ReportsDir | Out-Null
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          Mutation Testing & Coverage Analysis                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check for WSL with Ubuntu/Linux distro
$script:hasWslLinux = $false
$script:wslDistro = "Ubuntu"

function Test-WslLinux {
    try {
        # Try Ubuntu first
        $wslResult = wsl -d Ubuntu bash -c "echo ok" 2>&1
        if ($wslResult -eq "ok") {
            $script:hasWslLinux = $true
            $script:wslDistro = "Ubuntu"
            return $true
        }
    } catch {}
    
    try {
        # Try default WSL
        $wslResult = wsl bash -c "echo ok" 2>&1
        if ($wslResult -eq "ok") {
            $script:hasWslLinux = $true
            $script:wslDistro = ""
            return $true
        }
    } catch {}
    
    return $false
}

# Check dependencies
function Test-Dependencies {
    $missing = @()
    
    try {
        python -c "import coverage" 2>$null
        if ($LASTEXITCODE -ne 0) { $missing += "coverage" }
    } catch { $missing += "coverage" }
    
    try {
        python -c "import pytest_cov" 2>$null
        if ($LASTEXITCODE -ne 0) { $missing += "pytest-cov" }
    } catch { $missing += "pytest-cov" }
    
    # Check WSL for mutmut
    if (-not (Test-WslLinux)) {
        Write-Host "Note: WSL with Linux distro not detected." -ForegroundColor Yellow
        Write-Host "      Mutation testing will use discovery mode (no actual test execution)." -ForegroundColor Yellow
        Write-Host "      For full mutation testing, install Ubuntu WSL:" -ForegroundColor Yellow
        Write-Host "        wsl --install Ubuntu" -ForegroundColor Gray
        Write-Host ""
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "Missing dependencies: $($missing -join ', ')" -ForegroundColor Red
        Write-Host "Install with: pip install -e '.[dev]'" -ForegroundColor Yellow
        exit 1
    }
}

Test-Dependencies

# Default: run full e2e if neither specified
$runCoverage = $Coverage -or (-not $Coverage -and -not $Mutation -and -not $ShowSurvivors)
$runMutation = $Mutation -or (-not $Coverage -and -not $Mutation -and -not $ShowSurvivors)

# Show plan
Write-Host "Test Plan:" -ForegroundColor White
Write-Host "  Coverage:       $(if($runCoverage){'✓ Yes'}else{'- Skip'})" -ForegroundColor $(if($runCoverage){'Green'}else{'Gray'})
Write-Host "  Mutation:       $(if($runMutation){'✓ Yes (via WSL)'}else{'- Skip'})" -ForegroundColor $(if($runMutation){'Green'}else{'Gray'})
Write-Host "  HTML Reports:   $(if($generateHtml){'✓ Yes'}else{'- Skip'})" -ForegroundColor $(if($generateHtml){'Green'}else{'Gray'})
Write-Host "  Parallel:       $numWorkers workers" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would execute the above test plan" -ForegroundColor Magenta
    exit 0
}

Push-Location $ProjectRoot
$env:PYTHONPATH = "$ProjectRoot\scripts"

$overallStartTime = Get-Date

try {
    # ========================================
    # Coverage Analysis
    # ========================================
    if ($runCoverage) {
        Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor White
        Write-Host "│  Coverage Analysis                                             │" -ForegroundColor White
        Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor White
        
        # Build parallel args for pytest
        $parallelArgs = ""
        if ($numWorkers -gt 0) {
            $parallelArgs = "-n $numWorkers"
        }
        
        Write-Host "Running tests with coverage ($numWorkers workers)..." -ForegroundColor Gray
        Write-Host ""
        
        # Run pytest with coverage and parallel execution
        $coverageCmd = "python -m pytest tests/ $parallelArgs -q --tb=short --cov=scripts --cov=tests --cov-report=term-missing"
        Invoke-Expression $coverageCmd
        $coverageExitCode = $LASTEXITCODE
        
        if ($generateHtml) {
            $coverageHtmlDir = Join-Path $ReportsDir "coverage"
            Write-Host ""
            Write-Host "Generating HTML coverage report..." -ForegroundColor Gray
            $htmlCmd = "python -m pytest tests/ $parallelArgs -q --tb=no --cov=scripts --cov=tests --cov-report=html:$coverageHtmlDir"
            Invoke-Expression $htmlCmd 2>$null
            Write-Host "Coverage HTML: $coverageHtmlDir\index.html" -ForegroundColor Green
        }
        
        Write-Host ""
    }

    # ========================================
    # Mutation Testing
    # ========================================
    if ($runMutation) {
        if ($script:hasWslLinux) {
            # Use WSL + mutmut for full mutation testing
            Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor White
            Write-Host "│  Mutation Testing (via WSL + mutmut)                           │" -ForegroundColor White
            Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor White
            
            # Convert Windows path to WSL path
            $wslProjectRoot = $ProjectRoot -replace '\\', '/' -replace '^([A-Za-z]):', '/mnt/$1'.ToLower()
            $wslProjectRoot = $wslProjectRoot.Substring(0,5) + $wslProjectRoot.Substring(5,1).ToLower() + $wslProjectRoot.Substring(6)
            
            # Note: mutmut 3.x uses pyproject.toml for config, no CLI path options
            $mutmutArgs = ""
            
            if ($File) {
                Write-Host "Note: -File option not supported with mutmut 3.x" -ForegroundColor Yellow
                Write-Host "Configure paths_to_mutate in pyproject.toml instead" -ForegroundColor Gray
            }
            
            if ($Quick) {
                Write-Host "Mode: Using pyproject.toml config (mutmut 3.x)" -ForegroundColor Yellow
            }
            
            Write-Host "Running mutation tests via WSL ($script:wslDistro)..." -ForegroundColor Gray
            Write-Host "(This may take several minutes)" -ForegroundColor Gray
            Write-Host ""
            
            # Build WSL command prefix
            $wslPrefix = if ($script:wslDistro) { "wsl -d $script:wslDistro" } else { "wsl" }
            
            # Ensure pip and mutmut are installed in WSL
            Write-Host "Setting up mutmut in WSL..." -ForegroundColor Gray
            
            # Check if mutmut is available in WSL
            $checkMutmut = Invoke-Expression "$wslPrefix bash -c 'python3 -m mutmut --version'" 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host ""
                Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
                Write-Host "║  mutmut not found in WSL. Please run these commands:           ║" -ForegroundColor Yellow
                Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "  wsl -d Ubuntu bash" -ForegroundColor White
                Write-Host "  sudo apt-get update && sudo apt-get install -y python3-pip" -ForegroundColor White
                Write-Host "  pip3 install mutmut --break-system-packages" -ForegroundColor White
                Write-Host "  exit" -ForegroundColor White
                Write-Host ""
                Write-Host "Then re-run: .\run-mutation-tests.ps1" -ForegroundColor Gray
                Write-Host ""
                return
            }
            
            Write-Host "mutmut found: $checkMutmut" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Note: Mutmut generates mutants in WSL. Since tests require Windows" -ForegroundColor Yellow
            Write-Host "dependencies (Copilot SDK), mutation testing runs in discovery mode." -ForegroundColor Yellow
            Write-Host ""
            
            # Generate mutants only (skip test execution which requires Copilot SDK)
            Write-Host "Generating mutants..." -ForegroundColor Gray
            $wslCmd = "cd $wslProjectRoot && rm -rf mutants .mutmut-cache && python3 -m mutmut run --max-children 1 2>&1 || true"
            Invoke-Expression "$wslPrefix bash -c '$wslCmd'" | Out-Null
            
            Write-Host ""
            Write-Host "Mutation Points Discovered:" -ForegroundColor White
            $resultsOutput = Invoke-Expression "$wslPrefix bash -c 'cd $wslProjectRoot && python3 -m mutmut results 2>&1'" 2>&1
            
            # Count and summarize mutants
            $mutantLines = $resultsOutput | Where-Object { $_ -match "mutmut_\d+:" }
            $totalMutants = $mutantLines.Count
            
            Write-Host "  Total mutation points: $totalMutants" -ForegroundColor Cyan
            
            # Group by file
            $byFile = $mutantLines | ForEach-Object {
                if ($_ -match "scripts\.([^.]+)\.") { $Matches[1] }
            } | Group-Object | Sort-Object Count -Descending
            
            foreach ($group in $byFile) {
                Write-Host "    $($group.Name): $($group.Count) mutations" -ForegroundColor Gray
            }
            
            Write-Host ""
            Write-Host "These are code changes that SHOULD cause test failures." -ForegroundColor Yellow
            Write-Host "If tests pass with a mutation, that code path needs better coverage." -ForegroundColor Yellow
            
            # Save mutation points to JSON report
            $mutationReportPath = Join-Path $ReportsDir "mutation-points.json"
            $mutationReport = @{
                timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
                total_mutations = $totalMutants
                files = @{}
                note = "Discovery mode - mutants identified but not tested (Copilot SDK requires Windows)"
            }
            
            foreach ($group in $byFile) {
                $mutationReport.files[$group.Name] = $group.Count
            }
            
            $mutationReport | ConvertTo-Json -Depth 3 | Set-Content $mutationReportPath
            Write-Host "Report saved: $mutationReportPath" -ForegroundColor Green
            
            # Clean up mutants folder (temporary working directory)
            if (Test-Path "mutants") {
                Remove-Item -Recurse -Force "mutants" -ErrorAction SilentlyContinue
            }
            
        } else {
            # No WSL available - show setup instructions
            Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
            Write-Host "│  WSL Required for Mutation Testing                             │" -ForegroundColor Yellow
            Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Mutation testing requires WSL with Ubuntu and mutmut installed." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Setup instructions:" -ForegroundColor White
            Write-Host "  1. Install WSL:  wsl --install Ubuntu" -ForegroundColor Gray
            Write-Host "  2. Open WSL:     wsl -d Ubuntu bash" -ForegroundColor Gray
            Write-Host "  3. Install pip:  sudo apt-get update && sudo apt-get install -y python3-pip" -ForegroundColor Gray
            Write-Host "  4. Install mutmut: pip3 install mutmut --break-system-packages" -ForegroundColor Gray
            Write-Host "  5. Exit WSL:     exit" -ForegroundColor Gray
            Write-Host ""
            Write-Host "Then re-run: .\run-mutation-tests.ps1 -Mutation" -ForegroundColor Cyan
        }
        
        Write-Host ""
    }

    # ========================================
    # Show Surviving Mutants
    # ========================================
    if ($ShowSurvivors) {
        Write-Host "┌────────────────────────────────────────────────────────────────┐" -ForegroundColor Red
        Write-Host "│  Surviving Mutants (PROBLEMS TO FIX)                           │" -ForegroundColor Red
        Write-Host "└────────────────────────────────────────────────────────────────┘" -ForegroundColor Red
        Write-Host ""
        
        if (-not $script:hasWslLinux) {
            Write-Host "WSL with Linux distro required for -ShowSurvivors." -ForegroundColor Yellow
            Write-Host "Install Ubuntu WSL: wsl --install Ubuntu" -ForegroundColor Gray
        } elseif (-not (Test-Path ".mutmut-cache")) {
            Write-Host "No mutation cache found. Run mutation tests first:" -ForegroundColor Yellow
            Write-Host "  .\run-mutation-tests.ps1 -Mutation" -ForegroundColor Gray
        } else {
            # Convert Windows path to WSL path
            $wslProjectRoot = $ProjectRoot -replace '\\', '/' -replace '^([A-Za-z]):', '/mnt/$1'.ToLower()
            $wslProjectRoot = $wslProjectRoot.Substring(0,5) + $wslProjectRoot.Substring(5,1).ToLower() + $wslProjectRoot.Substring(6)
            
            # Build WSL command prefix
            $wslPrefix = if ($script:wslDistro) { "wsl -d $script:wslDistro" } else { "wsl" }
            
            Write-Host "Surviving mutants - tests failed to catch these changes:" -ForegroundColor Yellow
            Write-Host ""
            
            # Get results and show survivors
            $resultsOutput = Invoke-Expression "$wslPrefix bash -c 'cd $wslProjectRoot && python3 -m mutmut results'" 2>&1
            Write-Host $resultsOutput
            
            # Show each surviving mutant
            Write-Host ""
            Write-Host "Details of surviving mutants:" -ForegroundColor White
            
            # Get mutant IDs that survived
            $survivedIds = Invoke-Expression "$wslPrefix bash -c `"cd $wslProjectRoot && python3 -m mutmut results 2>&1 | grep -oP '^\s*\K\d+(?=\s)'`"" 2>&1
            
            foreach ($id in ($survivedIds -split "`n" | Where-Object { $_ -match '^\d+$' } | Select-Object -First 5)) {
                if ($id) {
                    Write-Host ""
                    Write-Host "--- Mutant $id ---" -ForegroundColor Cyan
                    $mutantDetail = Invoke-Expression "$wslPrefix bash -c 'cd $wslProjectRoot && python3 -m mutmut show $id'" 2>&1
                    foreach ($line in ($mutantDetail -split "`n")) {
                        if ($line -match '^\-') {
                            Write-Host $line -ForegroundColor Red
                        } elseif ($line -match '^\+') {
                            Write-Host $line -ForegroundColor Green
                        } else {
                            Write-Host $line -ForegroundColor Gray
                        }
                    }
                }
            }
            
            Write-Host ""
            Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Red
            Write-Host "RECOMMENDATION: Add tests to catch these mutations" -ForegroundColor Yellow
        }
        Write-Host ""
    }

    # ========================================
    # Summary
    # ========================================
    $overallEndTime = Get-Date
    $totalDuration = $overallEndTime - $overallStartTime
    
    Write-Host "────────────────────────────────────────────────────────────────" -ForegroundColor Gray
    Write-Host "Duration: $($totalDuration.ToString('mm\:ss'))" -ForegroundColor Yellow
    Write-Host "Reports:  $ReportsDir" -ForegroundColor Gray
    Write-Host ""
    
    if ($generateHtml) {
        Write-Host "Generated Reports:" -ForegroundColor White
        $coverageHtmlDir = Join-Path $ReportsDir "coverage"
        $mutmutHtmlDir = Join-Path $ReportsDir "mutation"
        
        if (Test-Path "$coverageHtmlDir\index.html") {
            Write-Host "  Coverage: $coverageHtmlDir\index.html" -ForegroundColor Gray
        }
        if (Test-Path $mutmutHtmlDir) {
            Write-Host "  Mutation: $mutmutHtmlDir" -ForegroundColor Gray
        }
        Write-Host ""
    }
    
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "  View survivors: .\run-mutation-tests.ps1 -ShowSurvivors" -ForegroundColor Gray
    Write-Host "  Open coverage:  Start-Process '$ReportsDir\coverage\index.html'" -ForegroundColor Gray

} finally {
    Pop-Location
}
