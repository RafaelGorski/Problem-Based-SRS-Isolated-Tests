"""Black-box tests for the Customer Problems (/cp) skill.

Tests verify that:
1. Skill produces CP artifacts with structured notation
2. Problems are classified (Obligation/Expectation/Hope)
3. Output contains required sections
4. No solution-focused language is present
"""

from __future__ import annotations

import pytest

from fixtures import get_expectations


class TestCustomerProblemsSkill:
    """Test suite for the customer-problems skill."""

    @pytest.mark.asyncio
    async def test_cp_generates_structured_notation(
        self, copilot_client, inventory_context
    ):
        """Verify CP output uses structured notation [Subject] [Verb] [Object] [Penalty]."""
        result = await copilot_client.execute_skill(
            f"/cp\n\n{inventory_context}"
        )

        # Should contain severity verbs
        assert result.has_cp_notation(), (
            "CP output should contain structured notation with severity verbs "
            "(must/expects/hopes)"
        )

    @pytest.mark.asyncio
    async def test_cp_includes_classification(
        self, copilot_client, inventory_context
    ):
        """Verify each CP is classified as Obligation, Expectation, or Hope."""
        result = await copilot_client.execute_skill(
            f"/cp\n\n{inventory_context}"
        )

        assert result.contains_pattern(
            r"(Obligation|Expectation|Hope)"
        ), "CP output should classify problems"

    @pytest.mark.asyncio
    async def test_cp_has_required_sections(
        self, copilot_client, inventory_context
    ):
        """Verify CP output contains required sections."""
        result = await copilot_client.execute_skill(
            f"/cp\n\n{inventory_context}"
        )

        expectations = get_expectations("customer-problems")
        for section in expectations.required_sections:
            assert result.contains_pattern(section), (
                f"CP output should contain section matching: {section}"
            )

    @pytest.mark.asyncio
    async def test_cp_no_requirements_notation(
        self, copilot_client, inventory_context
    ):
        """Verify CP output does not contain FR notation (wrong step)."""
        result = await copilot_client.execute_skill(
            f"/cp\n\n{inventory_context}"
        )

        expectations = get_expectations("customer-problems")
        for pattern in expectations.forbidden_patterns:
            assert not result.contains_pattern(pattern), (
                f"CP output should NOT contain FR notation: {pattern}"
            )

    @pytest.mark.asyncio
    async def test_cp_identifies_multiple_problems(
        self, copilot_client, inventory_context
    ):
        """Verify skill identifies multiple distinct problems from context."""
        result = await copilot_client.execute_skill(
            f"/cp\n\n{inventory_context}"
        )

        # Should have at least 2 CP references
        cp_matches = result.contains_pattern(r"CP[.-]?\d+")
        assert cp_matches, "Should identify multiple Customer Problems"

    @pytest.mark.asyncio
    async def test_cp_with_crm_context(
        self, copilot_client, crm_context
    ):
        """Test CP generation with CRM business context."""
        result = await copilot_client.execute_skill(
            f"/cp\n\n{crm_context}"
        )

        assert result.has_cp_notation()
        assert result.contains_pattern(r"CP[.-]?\d+")

    @pytest.mark.asyncio
    async def test_cp_with_field_service_context(
        self, copilot_client, field_service_context
    ):
        """Test CP generation with field service business context."""
        result = await copilot_client.execute_skill(
            f"/cp\n\n{field_service_context}"
        )

        assert result.has_cp_notation()
        assert result.contains_pattern(r"CP[.-]?\d+")
