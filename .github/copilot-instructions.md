# Copilot Instructions

## Quick Reference - Test Commands

| Command | What it does |
|---------|--------------|
| `.\run-all-tests.ps1` | Run **all 60 tests** once (default) |
| `.\run-all-tests.ps1 -Unit` | Run unit tests only (excludes e2e) |
| `.\run-all-tests.ps1 -E2E` | Run e2e tests only (`test_e2e_*.py`) |
| `.\run-all-tests.ps1 -Quick` | Quick smoke test (3 key tests) |
| `.\run-all-tests.ps1 -Full` | All tests + coverage + mutation |
| `.\run-all-tests.ps1 -Coverage -Html` | Coverage analysis with HTML report |

## Build, test, and lint commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests (clones skills from GitHub by default)
pytest

# Run tests in parallel (4 workers)
pytest -n 4

# Run single test file
pytest tests/test_customer_problems.py -v

# Run specific test
pytest tests/test_customer_problems.py::TestCustomerProblemsSkill::test_cp_generates_structured_notation -v

# Use local skills folder instead of GitHub
SKILL_DIR=C:\work\Problem-Based-SRS pytest

# Lint
ruff check .
```

## PowerShell helper scripts (primary entry point)

**Engineers should use these scripts as the main entry point for running tests**, not raw pytest commands. The scripts handle environment setup, provide better output formatting, and support common workflows.

```powershell
.\run-all-tests.ps1                   # Run ALL tests once (default)
.\run-all-tests.ps1 -Full             # All tests + coverage + mutation
.\run-all-tests.ps1 -Unit             # Unit tests only (excludes e2e)
.\run-all-tests.ps1 -E2E              # E2E tests only
.\run-all-tests.ps1 -Quick            # Quick smoke test (3 tests)
.\run-all-tests.ps1 -Coverage -Html   # Coverage with HTML report
.\verify-setup.ps1                    # Check environment before first run
```

### Standalone Scripts

| Script | Purpose |
|--------|---------|
| `run-all-tests.ps1` | **Master runner** - run all tests, coverage, mutation |
| `run-unit-tests.ps1` | Run tests with skill/test name filtering |
| `run-e2e-tests.ps1` | Run workflow-specific e2e tests (crm, microer) |
| `run-mutation-tests.ps1` | Coverage analysis + mutation discovery via WSL |
| `verify-setup.ps1` | Validates Python, Copilot CLI, and dependencies |
| `test-skill.ps1` | Interactively tests a single skill with fixtures |
| `generate-report.ps1` | Generates test reports (console, JUnit XML, HTML) |

## High-level architecture

This is a black-box test suite for Problem-Based SRS agent skills using the GitHub Copilot SDK.

```
*.ps1                         # PowerShell helper scripts (first-class artifacts)
scripts/                      # Python modules
  copilot_client.py           # CopilotClient wrapper with SkillResult class
  skill_loader.py             # Load skills from local path or GitHub
  fixtures.py                 # Test data (business contexts, expected patterns)
tests/                        # pytest test suites
  conftest.py                 # Shared fixtures (copilot_client, skill_loader)
  test_*.py                   # One file per skill under test
```

**Key classes:**
- `SkillTestClient` (copilot_client.py): Wraps CopilotClient for skill invocation
- `SkillResult`: Contains response content with pattern-matching helpers
- `SkillLoader` (skill_loader.py): Loads skills from local path or clones from GitHub

## Key conventions

- **Black-box only**: Tests validate skill outputs via pattern matching, not internal logic.
- **GitHub by default**: Skills are cloned from GitHub to ensure latest version. Set `SKILL_DIR` for local dev.
- **Parallel execution**: Use `-n N` or `-Parallel N` for parallel test execution with pytest-xdist.
- **Pattern validation**: Use `SkillResult.contains_pattern()` for flexible output matching.
- **Async tests**: All skill tests are async using pytest-asyncio.
- **Fixtures in scripts/**: Keep test data in `fixtures.py` for reuse across tests.
- **Environment config**: Set `SKILL_DIR` to use local skills, or `SKILL_REPO` to use a different GitHub repo.