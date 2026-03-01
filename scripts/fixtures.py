"""Test fixtures for Problem-Based SRS skill testing.

Contains sample business contexts, expected patterns, and test data
for validating skill outputs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BusinessContext:
    """A sample business context for testing skills."""

    name: str
    description: str
    domain: str
    stakeholders: list[str]


@dataclass
class ExpectedOutput:
    """Expected patterns and sections for skill output validation."""

    skill: str
    required_sections: list[str]
    required_patterns: list[str]
    forbidden_patterns: list[str]


# Sample business contexts for testing
SAMPLE_CONTEXTS = {
    "inventory_management": BusinessContext(
        name="Inventory Management System",
        description="""
A warehouse company tracks everything in spreadsheets and loses $50k/month due to errors.
They have 3 warehouses with 10,000+ SKUs. Staff manually enter inventory counts.
Current problems:
- Manual data entry causes frequent mistakes
- No real-time visibility into stock levels
- Reordering decisions are based on outdated information
- Compliance audits take 2 weeks to prepare
""",
        domain="Logistics",
        stakeholders=["Warehouse Manager", "Inventory Staff", "Compliance Officer"],
    ),
    "crm_system": BusinessContext(
        name="CRM Software",
        description="""
A company has strong difficulties to effectively build relationships with its clients
and is convinced that an information system such as a CRM can contribute to reduce
these difficulties.

Current situation:
- Communication with clients is ad-hoc and untracked
- Customer feedback is not systematically collected or analyzed
- Sales strategies are not aligned with customer behavior
- Client complaints often go unanswered
""",
        domain="Customer Relationship Management",
        stakeholders=["Sales Manager", "Account Manager", "Clients", "Marketing Team"],
    ),
    "field_service": BusinessContext(
        name="Field Service App",
        description="""
Field technicians cannot access customer data when they are on-site without internet.
Service calls take longer because technicians need to call the office for information.
Customer history is not available, leading to repeated diagnostics.

Problems:
- No offline access to customer records
- Service history lookup requires phone calls
- Parts availability not known until arriving at office
- Reports submitted days after service completion
""",
        domain="Field Services",
        stakeholders=["Field Technician", "Service Manager", "Customers", "Dispatch"],
    ),
}

# Expected outputs for each skill
SKILL_EXPECTATIONS = {
    "customer-problems": ExpectedOutput(
        skill="customer-problems",
        required_sections=["CP-", "Classification", "Statement"],
        required_patterns=[
            r"(must|expects?|hopes?|should)",  # Severity verbs
            r"(Obligation|Expectation|Hope)",  # Classification
            r"CP[.-]?\d+",  # CP numbering
        ],
        forbidden_patterns=[
            r"The .*? shall",  # FR notation (wrong step)
            r"needs .*? to (create|build|design)",  # CN notation (wrong step)
        ],
    ),
    "software-glance": ExpectedOutput(
        skill="software-glance",
        required_sections=["Software Glance", "Description", "System Boundary", "Interfaces"],
        required_patterns=[
            r"(Actors?|External Systems?)",
            r"(Web|LAN|API|Local)",  # Interface types
        ],
        forbidden_patterns=[
            r"The .*? shall",  # FR notation
            r"FR[.-]?\d+",  # FR numbering
        ],
    ),
    "customer-needs": ExpectedOutput(
        skill="customer-needs",
        required_sections=["CN-", "Outcome Class", "Traces to"],
        required_patterns=[
            r"needs? .*? to",  # CN notation
            r"(Information|Control|Construction|Entertainment)",  # Outcome classes
            r"CN[.-]?\d+",  # CN numbering
            r"CP[.-]?\d+",  # Traceability to CP
        ],
        forbidden_patterns=[
            r"The .*? shall",  # FR notation
        ],
    ),
    "software-vision": ExpectedOutput(
        skill="software-vision",
        required_sections=["Software Vision", "Positioning", "Stakeholder"],
        required_patterns=[
            r"(feature|capability)",
            r"(architecture|component)",
        ],
        forbidden_patterns=[],
    ),
    "functional-requirements": ExpectedOutput(
        skill="functional-requirements",
        required_sections=["FR-", "Statement", "Traceability", "Acceptance Criteria"],
        required_patterns=[
            r"(shall|should)",  # FR modal verbs
            r"FR[.-]?\d+",  # FR numbering
            r"CN[.-]?\d+",  # Traceability to CN
        ],
        forbidden_patterns=[],
    ),
    "zigzag-validator": ExpectedOutput(
        skill="zigzag-validator",
        required_sections=["Validation", "Traceability"],
        required_patterns=[
            r"(FR|CN|CP)[.-]?\d+",  # Artifact references
            r"(valid|invalid|gap|missing|orphan)",  # Validation terminology
        ],
        forbidden_patterns=[],
    ),
}


def get_context(name: str) -> BusinessContext:
    """Get a sample business context by name."""
    if name not in SAMPLE_CONTEXTS:
        raise ValueError(f"Unknown context: {name}. Available: {list(SAMPLE_CONTEXTS.keys())}")
    return SAMPLE_CONTEXTS[name]


def get_expectations(skill: str) -> ExpectedOutput:
    """Get expected output patterns for a skill."""
    if skill not in SKILL_EXPECTATIONS:
        raise ValueError(f"Unknown skill: {skill}. Available: {list(SKILL_EXPECTATIONS.keys())}")
    return SKILL_EXPECTATIONS[skill]


# Pre-built CP artifacts for multi-step testing
SAMPLE_CPS = """
## Customer Problems

### CP-001: Inventory Accuracy
**Statement:** The warehouse company must maintain accurate inventory counts otherwise faces $50k/month in losses due to stockouts and overordering.
**Classification:** Obligation

### CP-002: Real-time Visibility
**Statement:** The warehouse manager expects real-time visibility into stock levels otherwise cannot make timely reordering decisions.
**Classification:** Expectation

### CP-003: Compliance Preparation
**Statement:** The compliance officer must prepare audit documentation within regulatory timeframes otherwise faces fines and penalties.
**Classification:** Obligation
"""

SAMPLE_CNS = """
## Customer Needs

CN-001.1 - The warehouse manager needs the inventory system to know current stock levels at any time.
- Outcome Class: Information
- Traces to: CP-001, CP-002

CN-001.2 - The inventory staff needs the inventory system to be aware of discrepancies between physical and recorded counts.
- Outcome Class: Information
- Traces to: CP-001

CN-002.1 - The warehouse manager needs the inventory system to be informed when stock reaches reorder threshold.
- Outcome Class: Information
- Traces to: CP-002

CN-003.1 - The compliance officer needs the inventory system to generate audit-ready reports within minutes.
- Outcome Class: Construction
- Traces to: CP-003
"""

SAMPLE_SOFTWARE_GLANCE = """
## Software Glance: Warehouse Inventory System

### Description
The inventory system will provide a web interface for warehouse staff to manage inventory counts with barcode scanning. Managers will access dashboards showing real-time stock levels across all warehouses. The system will integrate with the existing ERP for purchase orders and maintain a local database for inventory records.

### System Boundary

**Actors:**
- Warehouse Staff: Perform physical counts, scan items
- Warehouse Manager: View reports, approve adjustments
- Compliance Officer: Generate audit reports

**External Systems:**
- ERP System: Purchase orders and supplier data

### Interfaces
| Interface | Type | Connected To | Purpose |
|-----------|------|--------------|---------|
| Staff Portal | Web | Warehouse Staff | Inventory counts and scanning |
| Manager Dashboard | Web | Warehouse Manager | Reports and analytics |
| ERP Integration | API | ERP System | Order synchronization |
"""
