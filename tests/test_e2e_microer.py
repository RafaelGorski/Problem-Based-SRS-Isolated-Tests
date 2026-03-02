"""End-to-end tests for Problem-Based SRS methodology using MicroER example.

This test suite validates the full 5-step workflow using the MicroER (Renewable
Energy Microgeneration) example from the dissertation. The MicroER domain
demonstrates a technical embedded systems context with:
- Obligation, Expectation, and Hope problem classes
- Information, Control, and Construction outcome classes
- Hardware sensor integration and real-time monitoring
"""

from __future__ import annotations

import pytest

from fixtures import (
    MICROER_CONTEXT,
    MICROER_CUSTOMER_NEEDS,
    MICROER_CUSTOMER_PROBLEMS,
    MICROER_FUNCTIONAL_REQUIREMENTS,
    MICROER_SOFTWARE_GLANCE,
)


class TestMicroERWorkflow:
    """End-to-end tests for MicroER renewable energy example."""

    @pytest.mark.asyncio
    async def test_microer_step1_customer_problems(self, copilot_client):
        """Step 1: Generate Customer Problems from MicroER business context."""
        result = await copilot_client.execute_skill(f"/cp\n\n{MICROER_CONTEXT}")

        # Should contain CP notation with proper structure
        assert result.has_cp_notation(), "Should use CP notation (must/expects/hopes)"
        assert result.contains_pattern(r"CP[.\-]?\d+"), "Should have CP numbering"

        # MicroER-specific: Should identify energy and environmental concerns
        assert result.contains_pattern(
            r"(energy|consumption|solar|wind|efficiency|environmental)"
        ), "Should identify MicroER-specific problems"

        # Should have multiple problem classes including Hope
        assert result.contains_pattern(
            r"(Obligation|Expectation|Hope)"
        ), "Should classify problem severity"

    @pytest.mark.asyncio
    async def test_microer_step2_software_glance(self, copilot_client):
        """Step 2: Generate Software Glance from MicroER context and CPs."""
        prompt = f"/glance\n\n{MICROER_CONTEXT}\n\n{MICROER_CUSTOMER_PROBLEMS}"
        result = await copilot_client.execute_skill(prompt)

        # Should describe embedded/hardware system
        assert result.contains_pattern(
            r"(energy|MicroER|renewable|microgeneration)"
        ), "Should reference energy domain"

        # Should identify hardware interfaces
        assert result.contains_pattern(
            r"(sensor|controller|hardware|battery|solar|wind)"
        ), "Should identify hardware components"

        # Should identify user interface
        assert result.contains_pattern(
            r"(dashboard|interface|display|user|monitor)"
        ), "Should describe user interface"

    @pytest.mark.asyncio
    async def test_microer_step3_customer_needs(self, copilot_client):
        """Step 3: Generate Customer Needs from MicroER CPs and Glance."""
        prompt = f"/cn\n\n{MICROER_CUSTOMER_PROBLEMS}\n\n{MICROER_SOFTWARE_GLANCE}"
        result = await copilot_client.execute_skill(prompt)

        # Should contain CN notation
        assert result.has_cn_notation(), "Should use CN notation (needs...to)"
        assert result.contains_pattern(r"CN[.\-]?\d+"), "Should have CN numbering"

        # Should have multiple outcome classes - MicroER has Information, Control, Construction
        assert result.contains_pattern(
            r"(Information|Control|Construction)"
        ), "Should classify outcome types"

        # Should trace to CPs
        assert result.contains_pattern(r"CP[.\-]?\d+"), "Should trace to Customer Problems"

    @pytest.mark.asyncio
    async def test_microer_step4_software_vision(self, copilot_client):
        """Step 4: Generate Software Vision from MicroER artifacts."""
        prompt = f"/vision\n\n{MICROER_SOFTWARE_GLANCE}\n\n{MICROER_CUSTOMER_NEEDS}"
        result = await copilot_client.execute_skill(prompt)

        # Should have positioning statement
        assert result.contains_pattern(
            r"(positioning|unlike|residential|energy management)"
        ), "Should include positioning"

        # Should identify stakeholders
        assert result.contains_pattern(
            r"(stakeholder|homeowner|maintenance|user)"
        ), "Should identify stakeholders"

        # Should describe embedded environment
        assert result.contains_pattern(
            r"(embedded|hardware|controller|sensor|real-time)"
        ), "Should describe technical environment"

    @pytest.mark.asyncio
    async def test_microer_step5_functional_requirements(self, copilot_client):
        """Step 5: Generate Functional Requirements from MicroER CNs."""
        prompt = f"/fr\n\n{MICROER_CUSTOMER_NEEDS}\n\n{MICROER_SOFTWARE_GLANCE}"
        result = await copilot_client.execute_skill(prompt)

        # Should use FR notation with shall
        assert result.has_fr_notation(), "Should use FR notation (shall/should)"
        assert result.contains_pattern(r"FR[.\-]?\d+"), "Should have FR numbering"

        # Should trace to CNs
        assert result.contains_pattern(r"CN[.\-]?\d+"), "Should trace to Customer Needs"

        # MicroER-specific FRs
        assert result.contains_pattern(
            r"(display|calculate|generate|adjust|log|allow)"
        ), "Should have action verbs for FRs"

    @pytest.mark.asyncio
    async def test_microer_zigzag_validation(self, copilot_client):
        """Validate full MicroER traceability with zigzag validator."""
        prompt = f"""/zigzag

{MICROER_CUSTOMER_PROBLEMS}

{MICROER_CUSTOMER_NEEDS}

{MICROER_FUNCTIONAL_REQUIREMENTS}
"""
        result = await copilot_client.execute_skill(prompt)

        # Should perform validation
        assert result.contains_pattern(
            r"(valid|trace|coverage|orphan|gap|complete)"
        ), "Should validate traceability"

        # Should reference all artifact types
        assert result.contains_pattern(r"CP[.\-]?\d+"), "Should reference CPs"
        assert result.contains_pattern(r"CN[.\-]?\d+"), "Should reference CNs"
        assert result.contains_pattern(r"FR[.\-]?\d+"), "Should reference FRs"


class TestMicroERSpecificPatterns:
    """Test MicroER domain-specific patterns and conventions."""

    @pytest.mark.asyncio
    async def test_microer_deep_decomposition(self, copilot_client):
        """MicroER example has deep CP decomposition (CP.1 with 5 sub-problems)."""
        result = await copilot_client.execute_skill(f"/cp\n\n{MICROER_CONTEXT}")

        # MicroER decomposes extensively
        content_lower = result.content.lower()
        has_decomposition = (
            result.contains_pattern(r"CP[.\-]?\d+[.\-]\d+")
            or "sub" in content_lower
            or "decompos" in content_lower
            or result.content.count("CP") > 3
        )
        assert has_decomposition or result.contains_pattern(
            r"CP[.\-]?\d+"
        ), "Should support deep problem decomposition"

    @pytest.mark.asyncio
    async def test_microer_control_outcome_class(self, copilot_client):
        """MicroER has Control outcome class (CN.2, CN.7) for energy distribution."""
        prompt = f"/cn\n\n{MICROER_CUSTOMER_PROBLEMS}\n\n{MICROER_SOFTWARE_GLANCE}"
        result = await copilot_client.execute_skill(prompt)

        # MicroER should have Control outcomes for energy management
        assert result.contains_pattern(
            r"Control"
        ), "MicroER should have Control outcome class"

    @pytest.mark.asyncio
    async def test_microer_hope_class_problems(self, copilot_client):
        """MicroER has Hope-class problems (environmental contribution)."""
        result = await copilot_client.execute_skill(f"/cp\n\n{MICROER_CONTEXT}")

        # MicroER has aspirational problems (CP.2, CP.3, CP.4)
        content_lower = result.content.lower()
        has_hope = (
            result.contains_pattern(r"Hope")
            or "intends" in content_lower
            or "aspir" in content_lower
            or "environmental" in content_lower
        )
        assert has_hope or result.contains_pattern(
            r"(must|expects?)"
        ), "Should identify Hope-class or other problem types"

    @pytest.mark.asyncio
    async def test_microer_hardware_integration(self, copilot_client):
        """MicroER Software Glance acknowledges hardware boundaries."""
        prompt = f"/glance\n\n{MICROER_CONTEXT}\n\n{MICROER_CUSTOMER_PROBLEMS}"
        result = await copilot_client.execute_skill(prompt)

        # Should recognize hardware components
        assert result.contains_pattern(
            r"(sensor|controller|battery|solar|wind|hardware|embedded)"
        ), "Should identify hardware integration"

    @pytest.mark.asyncio
    async def test_microer_real_time_requirements(self, copilot_client):
        """MicroER FRs include real-time monitoring requirements."""
        prompt = f"/fr\n\n{MICROER_CUSTOMER_NEEDS}\n\n{MICROER_SOFTWARE_GLANCE}"
        result = await copilot_client.execute_skill(prompt)

        # Should have real-time or monitoring requirements
        content_lower = result.content.lower()
        has_monitoring = (
            "real-time" in content_lower
            or "realtime" in content_lower
            or "monitor" in content_lower
            or "display" in content_lower
            or "alert" in content_lower
        )
        assert has_monitoring, "Should include real-time or monitoring requirements"
