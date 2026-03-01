"""Black-box tests for the Software Vision (/vision) skill.

Tests verify that:
1. Skill produces vision document with positioning
2. Stakeholders are identified
3. Features are listed
4. Architecture direction is provided
"""

from __future__ import annotations

import pytest

from fixtures import get_expectations


class TestSoftwareVisionSkill:
    """Test suite for the software-vision skill."""

    @pytest.mark.asyncio
    async def test_vision_has_positioning(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify vision includes positioning statement."""
        prompt = f"/vision\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_section("Vision") or result.contains_section(
            "Positioning"
        ), "Vision should contain positioning section"

    @pytest.mark.asyncio
    async def test_vision_identifies_stakeholders(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify vision identifies stakeholders."""
        prompt = f"/vision\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("software-vision")
        assert result.contains_section("Stakeholder") or result.contains_pattern(
            r"(stakeholder|user|actor)"
        ), "Vision should identify stakeholders"

    @pytest.mark.asyncio
    async def test_vision_lists_features(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify vision lists major features."""
        prompt = f"/vision\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("software-vision")
        assert result.contains_pattern(
            r"(feature|capability)"
        ), "Vision should list features or capabilities"

    @pytest.mark.asyncio
    async def test_vision_references_cns(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify vision traces back to Customer Needs."""
        prompt = f"/vision\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_pattern(r"CN[.-]?\d+"), (
            "Vision should reference Customer Needs"
        )
