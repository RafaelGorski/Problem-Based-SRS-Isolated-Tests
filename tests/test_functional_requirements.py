"""Black-box tests for the Functional Requirements (/fr) skill.

Tests verify that:
1. Skill produces FR artifacts with "shall" notation
2. Each FR traces to a Customer Need
3. FRs have acceptance criteria
4. Output follows structured notation
"""

from __future__ import annotations

import pytest

from fixtures import get_expectations, SAMPLE_CNS


class TestFunctionalRequirementsSkill:
    """Test suite for the functional-requirements skill."""

    @pytest.mark.asyncio
    async def test_fr_uses_shall_notation(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify FR output uses 'shall' or 'should' notation."""
        prompt = f"/fr\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Vision:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        assert result.has_fr_notation(), (
            "FR output should contain 'shall' or 'should' notation"
        )

    @pytest.mark.asyncio
    async def test_fr_has_numbering(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify FRs have proper numbering."""
        prompt = f"/fr\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Vision:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("functional-requirements")
        assert result.contains_pattern(r"FR[.-]?\d+"), (
            "FR output should have numbered identifiers"
        )

    @pytest.mark.asyncio
    async def test_fr_traces_to_cn(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify FRs trace back to Customer Needs."""
        prompt = f"/fr\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Vision:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("functional-requirements")
        assert result.contains_pattern(r"CN[.-]?\d+"), (
            "FR output should trace to Customer Needs"
        )

    @pytest.mark.asyncio
    async def test_fr_has_required_sections(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify FR output contains required sections."""
        prompt = f"/fr\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Vision:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("functional-requirements")
        section_found = any(
            result.contains_pattern(section)
            for section in expectations.required_sections
        )
        assert section_found, (
            f"FR output should contain one of: {expectations.required_sections}"
        )

    @pytest.mark.asyncio
    async def test_fr_has_acceptance_criteria(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify FRs include acceptance criteria."""
        prompt = f"/fr\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Vision:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_pattern(
            r"(Acceptance Criteria|acceptance criteria|\[\s*\])"
        ), "FR should include acceptance criteria"

    @pytest.mark.asyncio
    async def test_fr_multiple_requirements(
        self, copilot_client, sample_cns, sample_software_glance
    ):
        """Verify skill generates multiple FRs from multiple CNs."""
        prompt = f"/fr\n\nCustomer Needs:\n{sample_cns}\n\nSoftware Vision:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        # Check for multiple FR references
        import re

        matches = re.findall(r"FR[.-]?\d+", result.content)
        unique_frs = set(matches)
        assert len(unique_frs) >= 2, (
            f"Should generate multiple FRs, found: {unique_frs}"
        )
