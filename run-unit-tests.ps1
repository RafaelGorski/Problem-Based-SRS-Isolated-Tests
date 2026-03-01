<# 
.SYNOPSIS
    Run unit tests for Problem-Based SRS skills.

.DESCRIPTION
    Executes pytest unit tests with various options for filtering and output.
    Shows test progress (1/N, 2/N...), individual test durations, and total time.

.PARAMETER Skill
    Run tests for a specific skill (e.g., 'customer-problems', 'software-glance')

.PARAMETER Test
    Run a specific test by name pattern

.PARAMETER Verbose
    Show verbose output

.PARAMETER FailFast
    Stop on first failure

.PARAMETER Parallel
    Number of parallel workers (requires pytest-xdist)

.EXAMPLE
    .\run-unit-tests.ps1
    # Runs all unit tests

.EXAMPLE
    .\run-unit-tests.ps1 -Skill customer-problems
    # Runs only customer-problems skill tests

.EXAMPLE
    .\run-unit-tests.ps1 -Test "test_cp_generates" -Verbose
    # Runs tests matching pattern with verbose output

.EXAMPLE
    .\run-unit-tests.ps1 -FailFast
    # Stops on first failure

.EXAMPLE
    .\run-unit-tests.ps1 -Parallel 4
    # Runs tests with 4 parallel workers

.EXAMPLE
    .\run-unit-tests.ps1 -Sequential
    # Runs tests sequentially (no parallel)
#>

param(
    [ValidateSet('customer-problems', 'software-glance', 'customer-needs', 
                 'software-vision', 'functional-requirements', 'zigzag-validator',
                 'complexity-analysis', 'problem-based-srs', '')]
    [string]$Skill = '',
    
    [string]$Test = '',
    
    [switch]$Verbose,
    
    [switch]$FailFast,
    
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
    
    # Python version
    $config.PythonVersion = (python --version 2>&1) -replace 'Python ', ''
    
    # Copilot CLI version
    try {
        $config.CopilotVersion = (copilot --version 2>&1) -replace 'GitHub Copilot CLI ', ''
    } catch {
        $config.CopilotVersion = 'Not installed'
    }
    
    # Skill source
    $config.SkillSource = if ($env:SKILL_SOURCE) { $env:SKILL_SOURCE } else { 'local' }
    $config.SkillDir = if ($env:SKILL_DIR) { $env:SKILL_DIR } else { 'C:\work\Problem-Based-SRS' }
    
    # Model (from copilot_client.py default)
    $config.Model = if ($env:COPILOT_MODEL) { $env:COPILOT_MODEL } else { 'gpt-5' }
    
    # pytest version
    $config.PytestVersion = (python -c "import pytest; print(pytest.__version__)" 2>&1)
    
    # pytest-asyncio version
    $config.AsyncioVersion = (python -c "import pytest_asyncio; print(pytest_asyncio.__version__)" 2>&1)
    
    # pytest-xdist version (for parallel)
    try {
        $config.XdistVersion = (python -c "import xdist; print(xdist.__version__)" 2>&1)
    } catch {
        $config.XdistVersion = 'Not installed'
    }
    
    return $config
}

$config = Get-TestConfig

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Problem-Based SRS - Unit Tests" -ForegroundColor Cyan
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
Write-Host ""

# Build pytest arguments
$pytestArgs = @('tests/')

# Add skill filter
if ($Skill) {
    $testFile = "test_$($Skill -replace '-', '_').py"
    $pytestArgs = @("tests/$testFile")
    Write-Host "Skill: $Skill" -ForegroundColor Yellow
}

# Add test name filter
if ($Test) {
    $pytestArgs += "-k"
    $pytestArgs += "`"$Test`""
    Write-Host "Test filter: $Test" -ForegroundColor Yellow
}

# Add verbose flag
if ($Verbose) {
    $pytestArgs += "-v"
    $pytestArgs += "--tb=short"
}

# Add fail fast
if ($FailFast) {
    $pytestArgs += "-x"
}

# Add parallel execution - default to auto (uses CPU count) unless -Sequential is specified
if (-not $Sequential) {
    $numWorkers = if ($Workers -gt 0) { $Workers } elseif ($Parallel -gt 0) { $Parallel } else { 0 }
    if ($numWorkers -eq 0) {
        # Default to auto-detect workers based on CPU count
        $numWorkers = [Math]::Max(2, [int]([Environment]::ProcessorCount / 2))
    }
    Write-Host "Parallel workers: $numWorkers" -ForegroundColor Yellow
    $pytestArgs += "-n"
    $pytestArgs += "$numWorkers"
} else {
    Write-Host "Mode: Sequential (no parallelism)" -ForegroundColor Yellow
}

# Always show test durations
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
$env:PYTHONPATH = "$ProjectRoot\scripts"

Write-Host "Collecting tests..." -ForegroundColor Gray
$collectCmd = "python -m pytest $($pytestArgs -join ' ') --collect-only -q"
$collectOutput = Invoke-Expression $collectCmd 2>&1
$testLines = $collectOutput | Where-Object { $_ -match '<Coroutine test_|::test_' }
$testCount = $testLines.Count

# Build test name lookup for numbering during execution
$testNames = @{}
$i = 1
foreach ($test in $testLines) {
    $shortName = $test -replace '.*<Coroutine\s+', '' -replace '>.*', '' -replace '.*::', ''
    $testNames[$shortName] = $i
    $i++
}

if ($testCount -gt 0) {
    Write-Host ""
    Write-Host "Tests to execute: $testCount total" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "No tests collected!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Run tests with real-time output parsing to show test numbers
try {
    $startTime = Get-Date
    $runCmd = "python -m pytest $($pytestArgs -join ' ')"
    
    # Create process to capture output line by line
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = "python"
    $pinfo.Arguments = "-m pytest $($pytestArgs -join ' ')"
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true
    $pinfo.WorkingDirectory = $ProjectRoot
    $pinfo.EnvironmentVariables["PYTHONPATH"] = "$ProjectRoot\scripts"
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $pinfo
    $process.Start() | Out-Null
    
    $currentTestNum = 0
    $seenTests = @{}  # Track already-counted tests
    $lastTestTime = $startTime  # Track time between tests
    
    # Read output line by line
    while (!$process.StandardOutput.EndOfStream) {
        $line = $process.StandardOutput.ReadLine()
        
        # Check for sequential mode: "tests/file.py::Class::test_name PASSED"
        if ($line -match '(.+::test_\w+)\s+(PASSED|FAILED|SKIPPED|ERROR)') {
            $fullTestName = $matches[1]
            $status = $matches[2]
            $shortName = $fullTestName -replace '.*::', ''
            
            # Only count if not already seen (avoid duplicates from summary)
            if (-not $seenTests.ContainsKey($fullTestName)) {
                $seenTests[$fullTestName] = $true
                $currentTestNum++
                $now = Get-Date
                $elapsed = ($now - $startTime).TotalSeconds
                $testDuration = ($now - $lastTestTime).TotalSeconds
                $lastTestTime = $now
                
                # Color based on status
                $color = switch ($status) {
                    'PASSED' { 'Green' }
                    'FAILED' { 'Red' }
                    'SKIPPED' { 'Yellow' }
                    'ERROR' { 'Magenta' }
                    default { 'White' }
                }
                
                Write-Host "  [$currentTestNum/$testCount] " -NoNewline -ForegroundColor White
                Write-Host "$shortName " -NoNewline -ForegroundColor White
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
            
            # Only count if not already seen
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
        # Show durations section
        elseif ($line -match '^\s*\d+\.\d+s\s+(call|setup|teardown)\s+') {
            Write-Host $line -ForegroundColor Gray
        }
        # Show slowest durations header
        elseif ($line -match 'slowest.*durations') {
            Write-Host ""
            Write-Host $line -ForegroundColor White
        }
        # Show summary line
        elseif ($line -match '^\s*=+\s*\d+\s+(passed|failed)') {
            Write-Host ""
            Write-Host $line -ForegroundColor Cyan
        }
        # Show worker creation
        elseif ($line -match 'created:\s*\d+/\d+\s*workers') {
            Write-Host $line -ForegroundColor Cyan
        }
        # Show errors/failures detail
        elseif ($line -match '^(FAILURES|ERRORS|=====)') {
            Write-Host $line -ForegroundColor Red
        }
    }
    
    # Also read stderr
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
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed (exit code: $exitCode)" -ForegroundColor Red
}

exit $exitCode
