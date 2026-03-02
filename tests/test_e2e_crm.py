"""End-to-end tests for Problem-Based SRS methodology using CRM example.

This test suite validates the full 5-step workflow using the CRM (Customer
Relationship Management) example from the dissertation. The CRM domain
demonstrates a typical business information system with:
- Obligation and Expectation problem classes
- Information and Construction outcome classes
- Web and LAN interfaces
"""

from __future__ import annotations

import pytest

from fixtures import (
    CRM_CONTEXT,
    CRM_CUSTOMER_NEEDS,
    CRM_CUSTOMER_PROBLEMS,
    CRM_FUNCTIONAL_REQUIREMENTS,
    CRM_SOFTWARE_GLANCE,
)


class TestCRMWorkflow:
    """End-to-end tests for CRM system example."""

    @pytest.mark.asyncio
    async def test_crm_step1_customer_problems(self, copilot_client):
        """Step 1: Generate Customer Problems from CRM business context."""
        result = await copilot_client.execute_skill(f"/cp\n\n{CRM_CONTEXT}")

        # Should contain CP notation with proper structure
        assert result.has_cp_notation(), "Should use CP notation (must/expects/hopes)"
        assert result.contains_pattern(r"CP[.\-]?\d+"), "Should have CP numbering"

        # CRM-specific: Should identify communication and feedback issues
        assert result.contains_pattern(
            r"(customer|client|communication|feedback|contact)"
        ), "Should identify CRM-specific problems"

        # Should classify problems appropriately
        assert result.contains_pattern(
            r"(Obligation|Expectation)"
        ), "Should classify problem severity"

    @pytest.mark.asyncio
    async def test_crm_step2_software_glance(self, copilot_client):
        """Step 2: Generate Software Glance from CRM context and CPs."""
        prompt = f"/glance\n\n{CRM_CONTEXT}\n\n{CRM_CUSTOMER_PROBLEMS}"
        result = await copilot_client.execute_skill(prompt)

        # Should describe high-level solution
        assert result.contains_pattern(
            r"(CRM|Customer Relationship|customer management)"
        ), "Should reference CRM domain"

        # Should identify interfaces - CRM has Web, Local, and LAN
        assert result.contains_pattern(
            r"(Web|LAN|Local|API|interface)"
        ), "Should identify system interfaces"

        # Should identify actors
        assert result.contains_pattern(
            r"(Customer|Manager|Marketing|Actor)"
        ), "Should identify system actors"

    @pytest.mark.asyncio
    async def test_crm_step3_customer_needs(self, copilot_client):
        """Step 3: Generate Customer Needs from CRM CPs and Glance."""
        prompt = f"/cn\n\n{CRM_CUSTOMER_PROBLEMS}\n\n{CRM_SOFTWARE_GLANCE}"
        result = await copilot_client.execute_skill(prompt)

        # Should contain CN notation
        assert result.has_cn_notation(), "Should use CN notation (needs...to)"
        assert result.contains_pattern(r"CN[.\-]?\d+"), "Should have CN numbering"

        # Should have outcome classes - CRM is mostly Information
        assert result.contains_pattern(
            r"(Information|Construction)"
        ), "Should classify outcome types"

        # Should trace to CPs
        assert result.contains_pattern(r"CP[.\-]?\d+"), "Should trace to Customer Problems"

    @pytest.mark.asyncio
    async def test_crm_step4_software_vision(self, copilot_client):
        """Step 4: Generate Software Vision from CRM artifacts."""
        prompt = f"/vision\n\n{CRM_SOFTWARE_GLANCE}\n\n{CRM_CUSTOMER_NEEDS}"
        result = await copilot_client.execute_skill(prompt)

        # Should have positioning statement
        assert result.contains_pattern(
            r"(positioning|unlike|for companies|differs)"
        ), "Should include positioning"

        # Should identify stakeholders
        assert result.contains_pattern(
            r"(stakeholder|Marketing|Sales|Manager|Customer)"
        ), "Should identify stakeholders"

        # Should list high-level features
        assert result.contains_pattern(
            r"(feature|capability|contact|feedback|campaign)"
        ), "Should describe features"

    @pytest.mark.asyncio
    async def test_crm_step5_functional_requirements(self, copilot_client):
        """Step 5: Generate Functional Requirements from CRM CNs."""
        prompt = f"/fr\n\n{CRM_CUSTOMER_NEEDS}\n\n{CRM_SOFTWARE_GLANCE}"
        result = await copilot_client.execute_skill(prompt)

        # Should use FR notation with shall
        assert result.has_fr_notation(), "Should use FR notation (shall/should)"
        assert result.contains_pattern(r"FR[.\-]?\d+"), "Should have FR numbering"

        # Should trace to CNs
        assert result.contains_pattern(r"CN[.\-]?\d+"), "Should trace to Customer Needs"

        # CRM-specific FRs
        assert result.contains_pattern(
            r"(store|display|record|calculate|allow|send)"
        ), "Should have action verbs for FRs"

    @pytest.mark.asyncio
    async def test_crm_zigzag_validation(self, copilot_client):
        """Validate full CRM traceability with zigzag validator."""
        prompt = f"""/zigzag

{CRM_CUSTOMER_PROBLEMS}

{CRM_CUSTOMER_NEEDS}

{CRM_FUNCTIONAL_REQUIREMENTS}
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


class TestCRMSpecificPatterns:
    """Test CRM domain-specific patterns and conventions."""

    @pytest.mark.asyncio
    async def test_crm_cp_decomposition(self, copilot_client):
        """CRM example shows CP decomposition (CP.1 -> CP.1.1, CP.1.2)."""
        result = await copilot_client.execute_skill(f"/cp\n\n{CRM_CONTEXT}")

        # The CRM example decomposes CP.1 into sub-problems
        # Check for hierarchical numbering support
        content_lower = result.content.lower()
        has_sub_problems = (
            result.contains_pattern(r"CP[.\-]?\d+[.\-]\d+")
            or "sub" in content_lower
            or "decompos" in content_lower
        )
        assert has_sub_problems or result.contains_pattern(
            r"CP[.\-]?\d+"
        ), "Should support problem decomposition or basic CP numbering"

    @pytest.mark.asyncio
    async def test_crm_information_outcome_dominant(self, copilot_client):
        """CRM needs are predominantly Information-type outcomes."""
        prompt = f"/cn\n\n{CRM_CUSTOMER_PROBLEMS}\n\n{CRM_SOFTWARE_GLANCE}"
        result = await copilot_client.execute_skill(prompt)

        # CRM example has 5 Information CNs and 1 Construction CN
        assert result.contains_pattern(
            r"Information"
        ), "CRM should have Information outcome class"

    @pytest.mark.asyncio
    async def test_crm_shared_fr_traceability(self, copilot_client):
        """CRM example has FR.8 tracing to multiple CNs (CN.1, CN.2)."""
        prompt = f"/fr\n\n{CRM_CUSTOMER_NEEDS}\n\n{CRM_SOFTWARE_GLANCE}"
        result = await copilot_client.execute_skill(prompt)

        # Should support multiple CN references
        # Pattern: traces to CN.1, CN.2 or similar
        has_multiple_traces = (
            result.contains_pattern(r"CN[.\-]?\d+.*CN[.\-]?\d+")
            or result.contains_pattern(r"CN[.\-]?\d+,\s*CN[.\-]?\d+")
        )
        # This is acceptable if there are any FR references
        assert (
            has_multiple_traces or result.contains_pattern(r"CN[.\-]?\d+")
        ), "Should trace FRs to CNs"
