<# 
.SYNOPSIS
    Run end-to-end tests for Problem-Based SRS skills.

.DESCRIPTION
    Executes full workflow tests that exercise multiple skills in sequence,
    simulating real user workflows through the 5-step methodology.

.PARAMETER Workflow
    Run a specific workflow test (full, validation, quick)

.PARAMETER SkillSource
    Use 'local' or 'github' skills

.PARAMETER Timeout
    Timeout in seconds for each skill invocation (default: 120)

.PARAMETER Verbose
    Show detailed output including skill responses

.EXAMPLE
    .\run-e2e-tests.ps1
    # Runs all e2e tests with local skills

.EXAMPLE
    .\run-e2e-tests.ps1 -Workflow quick -Verbose
    # Runs quick validation with verbose output

.EXAMPLE
    .\run-e2e-tests.ps1 -SkillSource github
    # Uses skills from GitHub repository
#>

param(
    [ValidateSet('full', 'validation', 'quick', '')]
    [string]$Workflow = '',
    
    [ValidateSet('local', 'github')]
    [string]$SkillSource = 'local',
    
    [int]$Timeout = 120,
    
    [switch]$Verbose,
    
    [switch]$DryRun,
    
    [switch]$Sequential,
    
    [int]$Parallel = 0,
    
    [Alias('n')]
    [int]$Workers = 0
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot

# Get configuration info
function Get-TestConfig {
    $config = @{}
    $config.PythonVersion = (python --version 2>&1) -replace 'Python ', ''
    try {
        $config.CopilotVersion = (copilot --version 2>&1) -replace 'GitHub Copilot CLI ', ''
    } catch {
        $config.CopilotVersion = 'Not installed'
    }
    $config.SkillSource = $SkillSource
    $config.SkillDir = if ($env:SKILL_DIR) { $env:SKILL_DIR } else { 'C:\work\Problem-Based-SRS' }
    $config.Model = if ($env:COPILOT_MODEL) { $env:COPILOT_MODEL } else { 'gpt-5' }
    $config.PytestVersion = (python -c "import pytest; print(pytest.__version__)" 2>&1)
    $config.AsyncioVersion = (python -c "import pytest_asyncio; print(pytest_asyncio.__version__)" 2>&1)
    try {
        $config.XdistVersion = (python -c "import xdist; print(xdist.__version__)" 2>&1)
    } catch {
        $config.XdistVersion = 'Not installed'
    }
    return $config
}

$config = Get-TestConfig

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Problem-Based SRS - E2E Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Python:         $($config.PythonVersion)" -ForegroundColor Gray
Write-Host "  Copilot CLI:    $($config.CopilotVersion)" -ForegroundColor Gray
Write-Host "  Model:          $($config.Model)" -ForegroundColor Gray
Write-Host "  Skill Source:   $($config.SkillSource)" -ForegroundColor Gray
Write-Host "  Skill Dir:      $($config.SkillDir)" -ForegroundColor Gray
Write-Host "  pytest:         $($config.PytestVersion)" -ForegroundColor Gray
Write-Host "  pytest-asyncio: $($config.AsyncioVersion)" -ForegroundColor Gray
Write-Host "  pytest-xdist:   $($config.XdistVersion)" -ForegroundColor Gray
Write-Host "  Timeout:        ${Timeout}s" -ForegroundColor Gray
Write-Host ""

# Set environment
$env:SKILL_SOURCE = $SkillSource
$env:PYTHONPATH = "$ProjectRoot\scripts"

# Define test groups
$quickTests = @(
    "test_cp_generates_structured_notation",
    "test_cn_generates_structured_notation",
    "test_fr_uses_shall_notation"
)

$validationTests = @(
    "test_zigzag_validates_traceability",
    "test_zigzag_identifies_validation_status"
)

$fullWorkflowTests = @(
    "test_orchestrator_starts_with_step1",
    "test_cp_generates_structured_notation",
    "test_glance_produces_description",
    "test_cn_generates_structured_notation",
    "test_vision_has_positioning",
    "test_fr_uses_shall_notation",
    "test_zigzag_validates_traceability"
)

# Select tests based on workflow
$selectedTests = switch ($Workflow) {
    'quick' { $quickTests }
    'validation' { $validationTests }
    'full' { $fullWorkflowTests }
    default { @() }  # Run all
}

# Build pytest arguments
$pytestArgs = @('tests/')

if ($selectedTests.Count -gt 0) {
    $pattern = $selectedTests -join ' or '
    $pytestArgs += "-k"
    $pytestArgs += "`"$pattern`""
    Write-Host "Running: $($selectedTests.Count) selected tests" -ForegroundColor Yellow
}

if ($Verbose) {
    $pytestArgs += "-v"
    $pytestArgs += "-s"  # Show print statements
    $pytestArgs += "--tb=long"
}

# Add parallel execution - default to auto unless -Sequential is specified
if (-not $Sequential) {
    $numWorkers = if ($Workers -gt 0) { $Workers } elseif ($Parallel -gt 0) { $Parallel } else { 0 }
    if ($numWorkers -eq 0) {
        $numWorkers = [Math]::Max(2, [int]([Environment]::ProcessorCount / 2))
    }
    Write-Host "Parallel workers: $numWorkers" -ForegroundColor Yellow
    $pytestArgs += "-n"
    $pytestArgs += "$numWorkers"
} else {
    Write-Host "Mode: Sequential (no parallelism)" -ForegroundColor Yellow
}

$pytestArgs += "--durations=0"
$pytestArgs += "--no-header"

Write-Host ""
Write-Host "Command: python -m pytest $($pytestArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would execute the above command" -ForegroundColor Magenta
    exit 0
}

# Collect tests first to show count and list
Push-Location $ProjectRoot

Write-Host "Collecting tests..." -ForegroundColor Gray
$collectCmd = "python -m pytest $($pytestArgs -join ' ') --collect-only -q"
$collectOutput = Invoke-Expression $collectCmd 2>&1
$testLines = $collectOutput | Where-Object { $_ -match '<Coroutine test_|::test_' }
$testCount = $testLines.Count

if ($testCount -gt 0) {
    Write-Host ""
    Write-Host "Tests to execute: $testCount total" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "No tests collected!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Run tests with real-time output parsing
try {
    $startTime = Get-Date
    
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = "python"
    $pinfo.Arguments = "-m pytest $($pytestArgs -join ' ')"
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true
    $pinfo.WorkingDirectory = $ProjectRoot
    $pinfo.EnvironmentVariables["PYTHONPATH"] = "$ProjectRoot\scripts"
    $pinfo.EnvironmentVariables["SKILL_SOURCE"] = $SkillSource
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $pinfo
    $process.Start() | Out-Null
    
    $currentTestNum = 0
    $seenTests = @{}
    $lastTestTime = $startTime
    
    while (!$process.StandardOutput.EndOfStream) {
        $line = $process.StandardOutput.ReadLine()
        
        # Check for sequential mode: "tests/file.py::Class::test_name PASSED"
        if ($line -match '(.+::test_\w+)\s+(PASSED|FAILED|SKIPPED|ERROR)') {
            $fullTestName = $matches[1]
            $status = $matches[2]
            $shortName = $fullTestName -replace '.*::', ''
            
            if (-not $seenTests.ContainsKey($fullTestName)) {
                $seenTests[$fullTestName] = $true
                $currentTestNum++
                $now = Get-Date
                $testDuration = ($now - $lastTestTime).TotalSeconds
                $lastTestTime = $now
                
                $color = switch ($status) {
                    'PASSED' { 'Green' }
                    'FAILED' { 'Red' }
                    'SKIPPED' { 'Yellow' }
                    'ERROR' { 'Magenta' }
                    default { 'White' }
                }
                
                Write-Host "  [$currentTestNum/$testCount] $shortName " -NoNewline -ForegroundColor White
                Write-Host $status -NoNewline -ForegroundColor $color
                Write-Host " ($([Math]::Round($testDuration, 1))s)" -ForegroundColor Gray
            }
        }
        # Check for parallel worker output: "[gw0] PASSED tests/file.py::Class::test_name"
        elseif ($line -match '\[(gw\d+)\]\s+(PASSED|FAILED|SKIPPED|ERROR)\s+(.+::test_\w+)') {
            $worker = $matches[1]
            $status = $matches[2]
            $fullTestName = $matches[3]
            $shortName = $fullTestName -replace '.*::', ''
            
            if (-not $seenTests.ContainsKey($fullTestName)) {
                $seenTests[$fullTestName] = $true
                $currentTestNum++
                $now = Get-Date
                $elapsed = ($now - $startTime).TotalSeconds
                
                $color = switch ($status) {
                    'PASSED' { 'Green' }
                    'FAILED' { 'Red' }
                    'SKIPPED' { 'Yellow' }
                    'ERROR' { 'Magenta' }
                    default { 'White' }
                }
                
                Write-Host "  [$currentTestNum/$testCount] " -NoNewline -ForegroundColor White
                Write-Host "[$worker] " -NoNewline -ForegroundColor Cyan
                Write-Host "$shortName " -NoNewline -ForegroundColor White
                Write-Host $status -NoNewline -ForegroundColor $color
                Write-Host " (@ $([Math]::Round($elapsed, 1))s)" -ForegroundColor Gray
            }
        }
        elseif ($line -match '^\s*\d+\.\d+s\s+(call|setup|teardown)\s+') {
            Write-Host $line -ForegroundColor Gray
        }
        elseif ($line -match 'slowest.*durations') {
            Write-Host ""
            Write-Host $line -ForegroundColor White
        }
        elseif ($line -match '^\s*=+\s*\d+\s+(passed|failed)') {
            Write-Host ""
            Write-Host $line -ForegroundColor Cyan
        }
        elseif ($line -match 'created:\s*\d+/\d+\s*workers') {
            Write-Host $line -ForegroundColor Cyan
        }
        elseif ($line -match '^(FAILURES|ERRORS|=====)') {
            Write-Host $line -ForegroundColor Red
        }
    }
    
    $stderr = $process.StandardError.ReadToEnd()
    if ($stderr) {
        Write-Host $stderr -ForegroundColor Red
    }
    
    $process.WaitForExit()
    $exitCode = $process.ExitCode
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

if ($exitCode -eq 0) {
    Write-Host "✓ E2E tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ E2E tests failed (exit code: $exitCode)" -ForegroundColor Red
}

exit $exitCode
