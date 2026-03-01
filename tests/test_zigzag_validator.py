"""Black-box tests for the Zigzag Validator (/zigzag) skill.

Tests verify that:
1. Skill validates traceability chains (FR → CN → CP)
2. Identifies gaps and orphans
3. Reports validation status
"""

from __future__ import annotations

import pytest

from fixtures import get_expectations, SAMPLE_CPS, SAMPLE_CNS


SAMPLE_FRS = """
## Functional Requirements

### FR-001: Display Stock Levels
**Statement:** The inventory system shall display current stock levels for all SKUs.
**Traces to:** CN-001.1

### FR-002: Alert Low Stock
**Statement:** The inventory system shall alert users when stock reaches reorder threshold.
**Traces to:** CN-002.1

### FR-003: Generate Audit Report
**Statement:** The inventory system shall generate audit-ready reports within 5 minutes.
**Traces to:** CN-003.1
"""


class TestZigzagValidatorSkill:
    """Test suite for the zigzag-validator skill."""

    @pytest.mark.asyncio
    async def test_zigzag_validates_traceability(
        self, copilot_client, sample_cps
    ):
        """Verify zigzag validates the traceability chain."""
        prompt = f"/zigzag\n\nCustomer Problems:\n{sample_cps}\n\nCustomer Needs:\n{SAMPLE_CNS}\n\nFunctional Requirements:\n{SAMPLE_FRS}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("zigzag-validator")
        # Should reference artifacts
        assert result.contains_pattern(r"(FR|CN|CP)[.-]?\d+"), (
            "Zigzag should reference artifacts (FR, CN, CP)"
        )

    @pytest.mark.asyncio
    async def test_zigzag_identifies_validation_status(
        self, copilot_client, sample_cps
    ):
        """Verify zigzag reports validation terminology."""
        prompt = f"/zigzag\n\nCustomer Problems:\n{sample_cps}\n\nCustomer Needs:\n{SAMPLE_CNS}\n\nFunctional Requirements:\n{SAMPLE_FRS}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("zigzag-validator")
        assert result.contains_pattern(
            r"(valid|invalid|gap|missing|orphan|traced|complete)"
        ), "Zigzag should use validation terminology"

    @pytest.mark.asyncio
    async def test_zigzag_has_traceability_section(
        self, copilot_client, sample_cps
    ):
        """Verify zigzag contains traceability analysis."""
        prompt = f"/zigzag\n\nCustomer Problems:\n{sample_cps}\n\nCustomer Needs:\n{SAMPLE_CNS}\n\nFunctional Requirements:\n{SAMPLE_FRS}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("zigzag-validator")
        assert result.contains_section("Validation") or result.contains_section(
            "Traceability"
        ) or result.contains_pattern(r"(traceability|validation)"), (
            "Zigzag should contain validation or traceability section"
        )

    @pytest.mark.asyncio
    async def test_zigzag_with_incomplete_chain(self, copilot_client):
        """Verify zigzag detects gaps when chain is incomplete."""
        incomplete_cns = """
CN-001.1 - The manager needs the system to know stock levels.
- Traces to: CP-099  # Non-existent CP
"""
        prompt = f"/zigzag\n\nCustomer Problems:\n{SAMPLE_CPS}\n\nCustomer Needs:\n{incomplete_cns}"
        result = await copilot_client.execute_skill(prompt)

        # Should identify gaps or issues
        assert result.contains_pattern(
            r"(gap|missing|orphan|invalid|not found|unmatched)"
        ), "Zigzag should identify gaps in traceability"
