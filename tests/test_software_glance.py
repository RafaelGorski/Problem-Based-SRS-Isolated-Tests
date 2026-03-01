"""Black-box tests for the Software Glance (/glance) skill.

Tests verify that:
1. Skill produces a high-level system description
2. System boundary is defined (actors, external systems)
3. Interfaces are identified
4. Output stays conceptual (no FR notation)
"""

from __future__ import annotations

import pytest

from fixtures import get_expectations


class TestSoftwareGlanceSkill:
    """Test suite for the software-glance skill."""

    @pytest.mark.asyncio
    async def test_glance_produces_description(
        self, copilot_client, sample_cps, inventory_context
    ):
        """Verify glance output includes a narrative description."""
        prompt = f"/glance\n\nBusiness Context:\n{inventory_context}\n\nCustomer Problems:\n{sample_cps}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_section("Description") or result.contains_section(
            "Software Glance"
        ), "Glance should contain a Description section"

    @pytest.mark.asyncio
    async def test_glance_defines_system_boundary(
        self, copilot_client, sample_cps, inventory_context
    ):
        """Verify glance defines actors and external systems."""
        prompt = f"/glance\n\nBusiness Context:\n{inventory_context}\n\nCustomer Problems:\n{sample_cps}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("software-glance")
        assert result.contains_pattern(
            r"(Actors?|External Systems?)"
        ), "Glance should define system boundary with actors or external systems"

    @pytest.mark.asyncio
    async def test_glance_identifies_interfaces(
        self, copilot_client, sample_cps, inventory_context
    ):
        """Verify glance identifies interfaces with their types."""
        prompt = f"/glance\n\nBusiness Context:\n{inventory_context}\n\nCustomer Problems:\n{sample_cps}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_section("Interfaces") or result.contains_pattern(
            r"(Web|LAN|API|Local)"
        ), "Glance should identify interfaces"

    @pytest.mark.asyncio
    async def test_glance_no_fr_notation(
        self, copilot_client, sample_cps, inventory_context
    ):
        """Verify glance does not use FR notation (stays conceptual)."""
        prompt = f"/glance\n\nBusiness Context:\n{inventory_context}\n\nCustomer Problems:\n{sample_cps}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("software-glance")
        for pattern in expectations.forbidden_patterns:
            assert not result.contains_pattern(pattern), (
                f"Glance should NOT contain FR notation: {pattern}"
            )

    @pytest.mark.asyncio
    async def test_glance_traces_to_cps(
        self, copilot_client, sample_cps, inventory_context
    ):
        """Verify glance traces back to Customer Problems."""
        prompt = f"/glance\n\nBusiness Context:\n{inventory_context}\n\nCustomer Problems:\n{sample_cps}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_pattern(r"CP[.-]?\d+"), (
            "Glance should reference Customer Problems for traceability"
        )
