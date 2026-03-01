"""Black-box tests for the Problem-Based SRS orchestrator (/problem-based-srs) skill.

Tests verify that:
1. Skill orchestrates the full 5-step process
2. Detects current step from existing artifacts
3. Provides handoff guidance between steps
"""

from __future__ import annotations

import pytest


class TestProblemBasedSRSOrchestrator:
    """Test suite for the main problem-based-srs orchestrator skill."""

    @pytest.mark.asyncio
    async def test_orchestrator_starts_with_step1(
        self, copilot_client, inventory_context
    ):
        """Verify orchestrator begins with Step 1 (Customer Problems) when starting fresh."""
        prompt = f"/problem-based-srs\n\n{inventory_context}"
        result = await copilot_client.execute_skill(prompt)

        # Should start with CP generation or mention Step 1
        assert result.contains_pattern(
            r"(Step 1|Customer Problems?|CP[.-]?\d+)"
        ), "Orchestrator should start with Step 1 or produce CPs"

    @pytest.mark.asyncio
    async def test_orchestrator_detects_existing_cps(
        self, copilot_client, sample_cps
    ):
        """Verify orchestrator detects existing CPs and proceeds to next step."""
        prompt = f"/problem-based-srs\n\nI already have these Customer Problems:\n{sample_cps}"
        result = await copilot_client.execute_skill(prompt)

        # Should recognize existing CPs and suggest next step
        assert result.contains_pattern(
            r"(Step 2|Software Glance|next step|continue)"
        ) or result.has_cp_notation(), (
            "Orchestrator should detect existing artifacts"
        )

    @pytest.mark.asyncio
    async def test_orchestrator_provides_guidance(
        self, copilot_client, inventory_context
    ):
        """Verify orchestrator provides process guidance."""
        prompt = f"/problem-based-srs\n\n{inventory_context}"
        result = await copilot_client.execute_skill(prompt)

        # Should mention the methodology or steps
        assert result.contains_pattern(
            r"(Problem-Based|SRS|methodology|step|process)"
        ), "Orchestrator should provide methodology guidance"

    @pytest.mark.asyncio
    async def test_orchestrator_mentions_traceability(
        self, copilot_client, inventory_context
    ):
        """Verify orchestrator emphasizes traceability concept."""
        prompt = f"/problem-based-srs\n\nHelp me understand the methodology."
        result = await copilot_client.execute_skill(prompt)

        # Should mention traceability (core concept)
        assert result.contains_pattern(
            r"(traceability|trace|FR.*CN.*CP|WHY.*WHAT.*HOW)"
        ), "Orchestrator should emphasize traceability"
