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


# =====================================================================
# Real-world example: CRM System (from crm-example.md)
# =====================================================================
CRM_CONTEXT = """
The company has difficulties maintaining an effective relationship with its customers.
They believe a CRM (Customer Relationship Management) software system can help reduce
these difficulties.

Current situation:
- The company risks losing customers due to lack of communication channels
- Customer feedback is not systematically analyzed for planning
- Customers expect responses to their feedback but often don't receive them
- Sales strategies are not aligned with customer behavior patterns
- Sales projections are not available, leading to missed opportunities
"""

CRM_CUSTOMER_PROBLEMS = """
## Customer Problems

| ID | Statement | Class |
|----|-----------|-------|
| CP.1 | The company must ensure the existence of a communication channel with all customers, otherwise it risks losing customers, affecting marketing, promotions, feedback, and future sales. | Obligation |
| CP.1.1 | The company must ensure it can contact all of its customers. | Obligation |
| CP.1.2 | The company must ensure each customer is contacted regularly. | Obligation |
| CP.2 | The company must consider customer feedback statistics in planning, otherwise it creates customer dissatisfaction and loses market share. | Obligation |
| CP.3 | Customers expect the company to respond to their feedback, otherwise they become frustrated and company reputation decreases. | Expectation |
| CP.4 | The company must align sales strategies with customer behavior, otherwise it misses sales opportunities. | Obligation |
| CP.5 | The company must project sales, otherwise it loses opportunities and makes inadequate provisions. | Obligation |
"""

CRM_SOFTWARE_GLANCE = """
## Software Glance: CRM System

### Description
CRM software will interact with customers through a web interface for marketing campaigns,
feedback collection, and responses. It will provide local interfaces for the Manager to
view statistics and reports. The system stores customer data, feedback, and sales history
in a database and includes a LAN interface to the Sales Management software.

### System Boundary

**Actors:**
- Customers: Submit feedback, receive campaigns
- Manager: View statistics, generate reports
- Marketing Team: Execute campaigns

**External Systems:**
- Sales Management: Sales data and forecasts

### Interfaces
| Interface | Type | Connected To | Purpose |
|-----------|------|--------------|---------|
| Customer Portal | Web | Customers | Feedback and campaigns |
| Manager Dashboard | Local | Manager | Statistics and reports |
| Sales Integration | LAN | Sales Management | Sales data sync |
"""

CRM_CUSTOMER_NEEDS = """
## Customer Needs

| ID | Statement | Outcome Class | Traces To |
|----|-----------|---------------|-----------|
| CN.1 | The company needs a CRM software to know who its customers are and have updated contact information. | Information | CP.1.1 |
| CN.2 | The company needs a CRM software to be aware of when each customer was last contacted. | Information | CP.1.2 |
| CN.3 | The company needs a CRM software to know customer feedback statistics monthly. | Information | CP.2 |
| CN.4 | The company needs a CRM software to allow responding to customer feedback. | Construction | CP.3 |
| CN.5 | The company needs a CRM software to know customer behavior patterns. | Information | CP.4 |
| CN.6 | The company needs a CRM software to know projected sales forecasts quarterly. | Information | CP.5 |
"""

CRM_FUNCTIONAL_REQUIREMENTS = """
## Functional Requirements

| ID | Statement | Traces To |
|----|-----------|-----------|
| FR.1 | The CRM shall store and display customer contact information including name, email, phone, and address. | CN.1 |
| FR.2 | The CRM shall record the date of last contact for each customer. | CN.2 |
| FR.3 | The CRM shall display customers not contacted within a configurable period. | CN.2 |
| FR.4 | The CRM shall calculate and display feedback statistics by category monthly. | CN.3 |
| FR.5 | The CRM shall allow users to compose and send responses to customer feedback. | CN.4 |
| FR.6 | The CRM shall analyze and display customer purchase behavior patterns. | CN.5 |
| FR.7 | The CRM shall generate quarterly sales forecasts based on historical data. | CN.6 |
| FR.8 | The CRM shall send marketing campaigns to selected customer segments. | CN.1, CN.2 |
"""


# =====================================================================
# Real-world example: MicroER - Renewable Energy System (from microer-example.md)
# =====================================================================
MICROER_CONTEXT = """
A residential end user is concerned about rational energy use and has invested in a
renewable energy microgeneration unit with solar and wind sources. The user wants to:
- Reduce overall energy consumption
- Minimize environmental impact
- Adapt consumption patterns to energy availability
- Monitor system efficiency
"""

MICROER_CUSTOMER_PROBLEMS = """
## Customer Problems

| ID | Statement | Class |
|----|-----------|-------|
| CP.1 | The customer intends to reduce energy consumption to lower costs using a renewable microgeneration system based on solar and wind sources. | Obligation |
| CP.1.1 | The customer must reduce unnecessary energy consumption to reduce costs. | Obligation |
| CP.1.2 | The customer must change consumption patterns, otherwise unable to reduce consumption. | Obligation |
| CP.1.3 | The customer must monitor consumption patterns, otherwise unable to optimize usage. | Obligation |
| CP.1.4 | The customer must ensure generating unit efficiency, otherwise must consume from public grid. | Obligation |
| CP.1.5 | The customer must ensure maintenance status of generating unit, otherwise malfunction occurs. | Obligation |
| CP.2 | The customer intends to contribute to minimizing environmental impacts of public energy sources. | Hope |
| CP.2.1 | The customer must be aware of the environmental impact of their consumption. | Expectation |
| CP.2.2 | The customer intends to rationalize energy use. | Hope |
| CP.3 | The customer intends to contribute to reducing consumption pressure on regional/national energy matrix. | Hope |
| CP.4 | The customer intends to influence others toward energy and environmental causes. | Hope |
"""

MICROER_SOFTWARE_GLANCE = """
## Software Glance: MicroER System

### Description
MicroER software will integrate with hardware components including sensors and controllers.
It will provide a user interface for consumption monitoring and profile configuration.
The system collects data from solar and wind sources, controls energy distribution
based on user preferences, and displays efficiency and maintenance status.

### System Boundary

**Actors:**
- Homeowner: Configure profiles, view consumption
- Maintenance Tech: Monitor system health

**External Systems:**
- Solar Panel Sensors
- Wind Turbine Sensors
- Battery Management System
- Home Automation (optional)

### Interfaces
| Interface | Type | Connected To | Purpose |
|-----------|------|--------------|---------|
| User Dashboard | Local | Homeowner | Monitoring and configuration |
| Sensor Network | Hardware | Solar/Wind Sensors | Data collection |
| Battery Controller | Hardware | Battery System | Storage management |
| Home Integration | API | Home Automation | Load control |
"""

MICROER_CUSTOMER_NEEDS = """
## Customer Needs

| ID | Statement | Outcome Class | Traces To |
|----|-----------|---------------|-----------|
| CN.1 | The user needs MicroER to know current energy consumption in real-time. | Information | CP.1.1 |
| CN.2 | The user needs MicroER to control energy distribution based on consumption profiles. | Control | CP.1.2 |
| CN.3 | The user needs MicroER to know consumption patterns over time. | Information | CP.1.3 |
| CN.4 | The user needs MicroER to know generating unit efficiency status. | Information | CP.1.4 |
| CN.5 | The user needs MicroER to be aware of maintenance alerts. | Information | CP.1.5 |
| CN.6 | The user needs MicroER to know environmental impact metrics. | Information | CP.2.1 |
| CN.7 | The user needs MicroER to control load prioritization during low generation. | Control | CP.2.2 |
| CN.8 | The user needs MicroER to create consumption profiles. | Construction | CP.1.2 |
"""

MICROER_FUNCTIONAL_REQUIREMENTS = """
## Functional Requirements

| ID | Statement | Traces To |
|----|-----------|-----------|
| FR.1 | MicroER shall display real-time energy consumption in watts and kilowatt-hours. | CN.1 |
| FR.2 | MicroER shall allow users to define consumption profiles with load priorities. | CN.8 |
| FR.3 | MicroER shall automatically adjust energy distribution based on active profile. | CN.2 |
| FR.4 | MicroER shall display hourly, daily, weekly, and monthly consumption graphs. | CN.3 |
| FR.5 | MicroER shall calculate and display generation efficiency percentage. | CN.4 |
| FR.6 | MicroER shall generate maintenance alerts when efficiency drops below threshold. | CN.5 |
| FR.7 | MicroER shall calculate and display CO₂ offset compared to grid consumption. | CN.6 |
| FR.8 | MicroER shall reduce non-priority loads when generation falls below demand. | CN.7 |
| FR.9 | MicroER shall log all consumption and generation data for historical analysis. | CN.3 |
"""
