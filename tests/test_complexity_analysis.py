"""Black-box tests for the Complexity Analysis (/complexity) skill.

Tests verify that:
1. Skill performs Axiomatic Design analysis
2. Analyzes specification independence
3. Uses C/P completeness markers
"""

from __future__ import annotations

import pytest

from fixtures import SAMPLE_CNS


SAMPLE_FRS_FOR_COMPLEXITY = """
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

### FR-004: Update Stock Count
**Statement:** The inventory system shall update stock count when items are scanned.
**Traces to:** CN-001.2
"""


class TestComplexityAnalysisSkill:
    """Test suite for the complexity-analysis skill."""

    @pytest.mark.asyncio
    async def test_complexity_analyzes_independence(
        self, copilot_client
    ):
        """Verify complexity analysis checks specification independence."""
        prompt = f"/complexity\n\nCustomer Needs:\n{SAMPLE_CNS}\n\nFunctional Requirements:\n{SAMPLE_FRS_FOR_COMPLEXITY}"
        result = await copilot_client.execute_skill(prompt)

        # Should mention coupling or independence concepts
        assert result.contains_pattern(
            r"(coupled|uncoupled|independent|independence|decoupled)"
        ), "Complexity analysis should assess specification independence"

    @pytest.mark.asyncio
    async def test_complexity_uses_design_terminology(
        self, copilot_client
    ):
        """Verify complexity analysis uses Axiomatic Design terminology."""
        prompt = f"/complexity\n\nCustomer Needs:\n{SAMPLE_CNS}\n\nFunctional Requirements:\n{SAMPLE_FRS_FOR_COMPLEXITY}"
        result = await copilot_client.execute_skill(prompt)

        # Should use axiomatic design or complexity terminology
        assert result.contains_pattern(
            r"(Axiomatic|design|complexity|information content|matrix)"
        ), "Complexity analysis should use design terminology"

    @pytest.mark.asyncio
    async def test_complexity_references_artifacts(
        self, copilot_client
    ):
        """Verify complexity analysis references FR and CN artifacts."""
        prompt = f"/complexity\n\nCustomer Needs:\n{SAMPLE_CNS}\n\nFunctional Requirements:\n{SAMPLE_FRS_FOR_COMPLEXITY}"
        result = await copilot_client.execute_skill(prompt)

        assert result.contains_pattern(r"(FR|CN)[.-]?\d+"), (
            "Complexity analysis should reference artifacts"
        )

    @pytest.mark.asyncio
    async def test_complexity_provides_assessment(
        self, copilot_client
    ):
        """Verify complexity analysis provides quality assessment."""
        prompt = f"/complexity\n\nCustomer Needs:\n{SAMPLE_CNS}\n\nFunctional Requirements:\n{SAMPLE_FRS_FOR_COMPLEXITY}"
        result = await copilot_client.execute_skill(prompt)

        # Should provide some form of assessment
        assert result.contains_pattern(
            r"(quality|assessment|analysis|complete|partial|C/P|completeness)"
        ), "Complexity analysis should provide quality assessment"
