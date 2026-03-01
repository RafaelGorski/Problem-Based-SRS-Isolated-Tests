"""Black-box tests for the Customer Needs (/cn) skill.

Tests verify that:
1. Skill produces CN artifacts with structured notation
2. Each CN has an outcome class (Information/Control/Construction/Entertainment)
3. CNs trace back to CPs
4. Output follows [Noun] needs [System] to [Verb] [Object] pattern
"""

from __future__ import annotations

import pytest

from fixtures import get_expectations


class TestCustomerNeedsSkill:
    """Test suite for the customer-needs skill."""

    @pytest.mark.asyncio
    async def test_cn_generates_structured_notation(
        self, copilot_client, sample_cps, sample_software_glance
    ):
        """Verify CN output uses structured notation [Noun] needs [System] to [Verb]."""
        prompt = f"/cn\n\nCustomer Problems:\n{sample_cps}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        assert result.has_cn_notation(), (
            "CN output should contain structured notation 'needs ... to'"
        )

    @pytest.mark.asyncio
    async def test_cn_includes_outcome_class(
        self, copilot_client, sample_cps, sample_software_glance
    ):
        """Verify each CN has an outcome class assigned."""
        prompt = f"/cn\n\nCustomer Problems:\n{sample_cps}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_pattern(
            r"(Information|Control|Construction|Entertainment)"
        ), "CN output should include outcome class"

    @pytest.mark.asyncio
    async def test_cn_traces_to_cp(
        self, copilot_client, sample_cps, sample_software_glance
    ):
        """Verify CNs trace back to Customer Problems."""
        prompt = f"/cn\n\nCustomer Problems:\n{sample_cps}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("customer-needs")
        assert result.contains_pattern(r"CP[.-]?\d+"), (
            "CN output should trace to Customer Problems"
        )

    @pytest.mark.asyncio
    async def test_cn_has_numbering(
        self, copilot_client, sample_cps, sample_software_glance
    ):
        """Verify CNs have proper numbering."""
        prompt = f"/cn\n\nCustomer Problems:\n{sample_cps}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_pattern(r"CN[.-]?\d+"), (
            "CN output should have numbered identifiers"
        )

    @pytest.mark.asyncio
    async def test_cn_no_fr_notation(
        self, copilot_client, sample_cps, sample_software_glance
    ):
        """Verify CN output does not contain FR notation (wrong step)."""
        prompt = f"/cn\n\nCustomer Problems:\n{sample_cps}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        expectations = get_expectations("customer-needs")
        for pattern in expectations.forbidden_patterns:
            assert not result.contains_pattern(pattern), (
                f"CN output should NOT contain FR notation: {pattern}"
            )

    @pytest.mark.asyncio
    async def test_cn_covers_all_cps(
        self, copilot_client, sample_cps, sample_software_glance
    ):
        """Verify CNs address the provided Customer Problems."""
        prompt = f"/cn\n\nCustomer Problems:\n{sample_cps}\n\nSoftware Glance:\n{sample_software_glance}"
        result = await copilot_client.execute_skill(prompt)

        # Should reference multiple CPs
        assert result.contains_pattern(r"CP[.-]?001") or result.contains_pattern(
            r"CP[.-]?1\b"
        ), "CN should address CP-001"
