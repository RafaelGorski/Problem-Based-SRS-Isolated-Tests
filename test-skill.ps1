<# 
.SYNOPSIS
    Run a single skill interactively and inspect the output.

.DESCRIPTION
    Executes a single skill command and displays the full output for manual inspection.
    Useful for debugging test failures or understanding skill behavior.

.PARAMETER Skill
    The skill to test (customer-problems, software-glance, etc.)

.PARAMETER Context
    Custom business context to send to the skill

.PARAMETER UseFixture
    Use a predefined fixture context (inventory, crm, field-service)

.EXAMPLE
    .\test-skill.ps1 -Skill customer-problems -UseFixture inventory
    # Tests /cp skill with inventory context

.EXAMPLE
    .\test-skill.ps1 -Skill software-glance -Context "My custom context..."
    # Tests /glance with custom context
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('customer-problems', 'software-glance', 'customer-needs', 
                 'software-vision', 'functional-requirements', 'zigzag-validator',
                 'complexity-analysis', 'problem-based-srs')]
    [string]$Skill,
    
    [string]$Context = '',
    
    [ValidateSet('inventory', 'crm', 'field-service', '')]
    [string]$UseFixture = '',
    
    [switch]$ShowEvents
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
    $config.SkillSource = if ($env:SKILL_SOURCE) { $env:SKILL_SOURCE } else { 'local' }
    $config.SkillDir = if ($env:SKILL_DIR) { $env:SKILL_DIR } else { 'C:\work\Problem-Based-SRS' }
    $config.Model = if ($env:COPILOT_MODEL) { $env:COPILOT_MODEL } else { 'gpt-5' }
    return $config
}

$config = Get-TestConfig

# Map skill names to commands
$skillCommands = @{
    'customer-problems' = '/cp'
    'software-glance' = '/glance'
    'customer-needs' = '/cn'
    'software-vision' = '/vision'
    'functional-requirements' = '/fr'
    'zigzag-validator' = '/zigzag'
    'complexity-analysis' = '/complexity'
    'problem-based-srs' = '/problem-based-srs'
}

$command = $skillCommands[$Skill]

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Skill: $Skill" -ForegroundColor Cyan
Write-Host "  Command: $command" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Python:       $($config.PythonVersion)" -ForegroundColor Gray
Write-Host "  Copilot CLI:  $($config.CopilotVersion)" -ForegroundColor Gray
Write-Host "  Model:        $($config.Model)" -ForegroundColor Gray
Write-Host "  Skill Source: $($config.SkillSource)" -ForegroundColor Gray
Write-Host "  Skill Dir:    $($config.SkillDir)" -ForegroundColor Gray
Write-Host ""

# Build the Python script
$pythonScript = @"
import asyncio
import sys
sys.path.insert(0, r'$ProjectRoot\scripts')

from copilot_client import SkillTestClient
from fixtures import SAMPLE_CONTEXTS, SAMPLE_CPS, SAMPLE_CNS, SAMPLE_SOFTWARE_GLANCE

async def test_skill():
    # Get context
    context = '''$Context'''
    fixture = '$UseFixture'
    
    if fixture and not context:
        if fixture == 'inventory':
            context = SAMPLE_CONTEXTS['inventory_management'].description
        elif fixture == 'crm':
            context = SAMPLE_CONTEXTS['crm_system'].description
        elif fixture == 'field-service':
            context = SAMPLE_CONTEXTS['field_service'].description
    
    if not context:
        context = "A warehouse company loses \$50k/month due to inventory tracking errors in spreadsheets."
    
    print("Context:")
    print("-" * 40)
    print(context[:500] + "..." if len(context) > 500 else context)
    print("-" * 40)
    print()
    
    async with SkillTestClient() as client:
        prompt = f"$command\n\n{context}"
        
        print("Executing skill...")
        print()
        
        result = await client.execute_skill(prompt)
        
        print("=" * 60)
        print("SKILL OUTPUT")
        print("=" * 60)
        print(result.content)
        print("=" * 60)
        print()
        
        # Validation checks
        print("VALIDATION CHECKS:")
        print(f"  Has CP notation: {result.has_cp_notation()}")
        print(f"  Has CN notation: {result.has_cn_notation()}")
        print(f"  Has FR notation: {result.has_fr_notation()}")
        print(f"  Contains 'Obligation': {result.contains_pattern(r'Obligation')}")
        print(f"  Contains 'CP-': {result.contains_pattern(r'CP[.-]?\d+')}")
        print(f"  Contains 'CN-': {result.contains_pattern(r'CN[.-]?\d+')}")
        print(f"  Contains 'FR-': {result.contains_pattern(r'FR[.-]?\d+')}")
        
        if $($ShowEvents.ToString().ToLower()):
            print()
            print("EVENTS:")
            for event in result.events:
                print(f"  {event['type']}")

asyncio.run(test_skill())
"@

# Run the script
Push-Location $ProjectRoot
try {
    $env:PYTHONPATH = "$ProjectRoot\scripts"
    $startTime = Get-Date
    $pythonScript | python -
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

exit $exitCode
