<# 
.SYNOPSIS
    Verify test environment and prerequisites.

.DESCRIPTION
    Checks that all required tools and dependencies are properly installed
    and configured for running tests.

.PARAMETER Fix
    Attempt to fix issues automatically (install missing packages)

.EXAMPLE
    .\verify-setup.ps1
    # Checks environment and reports issues

.EXAMPLE
    .\verify-setup.ps1 -Fix
    # Checks and attempts to fix issues
#>

param(
    [switch]$Fix
)

$ErrorActionPreference = 'Continue'
$ProjectRoot = $PSScriptRoot
$hasErrors = $false

function Write-Check {
    param([string]$Name, [bool]$Passed, [string]$Details = '')
    if ($Passed) {
        Write-Host "  [✓] $Name" -ForegroundColor Green
        if ($Details) { Write-Host "      $Details" -ForegroundColor Gray }
    } else {
        Write-Host "  [✗] $Name" -ForegroundColor Red
        if ($Details) { Write-Host "      $Details" -ForegroundColor Yellow }
        $script:hasErrors = $true
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Environment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Python:" -ForegroundColor White
try {
    $pythonVersion = python --version 2>&1
    $versionMatch = $pythonVersion -match '(\d+)\.(\d+)'
    if ($versionMatch) {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        $passed = ($major -eq 3 -and $minor -ge 11) -or ($major -gt 3)
        Write-Check "Python version" $passed "$pythonVersion (requires 3.11+)"
    }
} catch {
    Write-Check "Python installed" $false "Python not found in PATH"
}

# Check pip packages
Write-Host ""
Write-Host "Python Packages:" -ForegroundColor White
$requiredPackages = @('pytest', 'pytest-asyncio')
foreach ($pkg in $requiredPackages) {
    $installed = python -m pip show $pkg 2>$null
    $passed = $LASTEXITCODE -eq 0
    if (-not $passed -and $Fix) {
        Write-Host "      Installing $pkg..." -ForegroundColor Yellow
        python -m pip install $pkg --quiet
        $passed = $LASTEXITCODE -eq 0
    }
    Write-Check $pkg $passed
}

# Check project installation
$projectInstalled = python -c "import scripts" 2>$null
$projectPassed = $LASTEXITCODE -eq 0
if (-not $projectPassed -and $Fix) {
    Write-Host "      Installing project..." -ForegroundColor Yellow
    Push-Location $ProjectRoot
    python -m pip install -e ".[dev]" --quiet
    $projectPassed = $LASTEXITCODE -eq 0
    Pop-Location
}
Write-Check "Project installed" $projectPassed "pip install -e .[dev]"

# Check Copilot CLI
Write-Host ""
Write-Host "Copilot CLI:" -ForegroundColor White
try {
    $copilotVersion = copilot --version 2>&1
    Write-Check "Copilot CLI installed" $true "$copilotVersion"
} catch {
    Write-Check "Copilot CLI installed" $false "Install from https://docs.github.com/copilot"
}

# Check skills directory
Write-Host ""
Write-Host "Skills:" -ForegroundColor White
$localSkillDir = $env:SKILL_DIR
if (-not $localSkillDir) { $localSkillDir = "C:\work\Problem-Based-SRS" }
$skillsExist = Test-Path "$localSkillDir\skills"
Write-Check "Local skills directory" $skillsExist $localSkillDir

if ($skillsExist) {
    $skillCount = (Get-ChildItem "$localSkillDir\skills" -Directory | Where-Object { 
        Test-Path "$($_.FullName)\SKILL.md" 
    }).Count
    Write-Check "Skills found" ($skillCount -gt 0) "$skillCount skills"
}

# Check test files
Write-Host ""
Write-Host "Test Files:" -ForegroundColor White
$testFiles = Get-ChildItem "$ProjectRoot\tests\test_*.py" -ErrorAction SilentlyContinue
Write-Check "Test files found" ($testFiles.Count -gt 0) "$($testFiles.Count) test files"

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($hasErrors) {
    Write-Host "  Some checks failed!" -ForegroundColor Red
    Write-Host "  Run with -Fix to attempt auto-repair" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "  All checks passed!" -ForegroundColor Green
    Write-Host "  Ready to run tests" -ForegroundColor Gray
    exit 0
}
