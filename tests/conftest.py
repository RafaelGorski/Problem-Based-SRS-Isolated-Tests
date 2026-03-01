"""Pytest configuration and fixtures for skill tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from copilot_client import SkillTestClient
from fixtures import SAMPLE_CONTEXTS, SAMPLE_CPS, SAMPLE_CNS, SAMPLE_SOFTWARE_GLANCE
from skill_loader import SkillLoader


@pytest.fixture(scope="module")
def skill_loader():
    """Provide a skill loader for the test module."""
    loader = SkillLoader()
    loader.load()
    yield loader
    loader.cleanup()


@pytest.fixture
def skill_dir(skill_loader: SkillLoader) -> Path:
    """Get the skills directory path."""
    return skill_loader.skill_dir


@pytest.fixture
async def copilot_client(skill_loader: SkillLoader):
    """Provide an async Copilot client for skill testing."""
    client = SkillTestClient(skill_dir=str(skill_loader.skill_dir))
    await client.start()
    yield client
    await client.stop()


@pytest.fixture
def inventory_context() -> str:
    """Get the inventory management business context."""
    return SAMPLE_CONTEXTS["inventory_management"].description


@pytest.fixture
def crm_context() -> str:
    """Get the CRM business context."""
    return SAMPLE_CONTEXTS["crm_system"].description


@pytest.fixture
def field_service_context() -> str:
    """Get the field service business context."""
    return SAMPLE_CONTEXTS["field_service"].description


@pytest.fixture
def sample_cps() -> str:
    """Get sample Customer Problems for multi-step testing."""
    return SAMPLE_CPS


@pytest.fixture
def sample_cns() -> str:
    """Get sample Customer Needs for multi-step testing."""
    return SAMPLE_CNS


@pytest.fixture
def sample_software_glance() -> str:
    """Get sample Software Glance for multi-step testing."""
    return SAMPLE_SOFTWARE_GLANCE
