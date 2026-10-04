import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

base_dir = r"c:\Users\USER\OneDrive\Desktop\Custom_API_Integration\FDE-9B-[YourName]-Batch01"
pres_dir = os.path.join(base_dir, "presentation")
os.makedirs(pres_dir, exist_ok=True)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Color Palette
NAVY = RGBColor(27, 54, 93)       # #1B365D - Primary Meridian Navy
TEAL = RGBColor(13, 148, 136)     # #0D9488 - Accent Teal
GOLD = RGBColor(217, 119, 6)      # #D97706 - Warning / Highlight Gold
CHARCOAL = RGBColor(30, 41, 59)   # #1E293B - Dark Text
SLATE = RGBColor(100, 116, 139)   # #64748B - Subtitle / Secondary
LIGHT_BG = RGBColor(248, 250, 252)# #F8FAFC - Slide BG
CARD_BG = RGBColor(255, 255, 255) # White
BORDER_CLR = RGBColor(226, 232, 240)

def set_slide_bg(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = LIGHT_BG

def add_header(slide, title_text, category_text="MERIDIAN MANUFACTURING LTD. | PRODUCTION INTEGRATION DEFENCE"):
    # Category / Super-header
    tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.4))
    tf_cat = tb_cat.text_frame
    tf_cat.word_wrap = True
    p_cat = tf_cat.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = TEAL

    # Main Title
    tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.5), Inches(0.8))
    tf_title = tb_title.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.size = Pt(22)
    p_title.font.bold = True
    p_title.font.color.rgb = NAVY

def add_card(slide, left, top, width, height, title, items, border_color=BORDER_CLR, header_color=NAVY):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = CARD_BG
    shape.line.color.rgb = border_color
    shape.line.width = Pt(1.5)
    
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.2)
    tf.margin_bottom = Inches(0.2)
    
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = header_color
    
    for item in items:
        p2 = tf.add_paragraph()
        p2.text = f"• {item}"
        p2.font.size = Pt(10)
        p2.font.color.rgb = CHARCOAL

# Slide 1: Title Slide
slide_layout = prs.slide_layouts[6]
s1 = prs.slides.add_slide(slide_layout)
set_slide_bg(s1)

tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(3.5))
tf1 = tb1.text_frame
p1 = tf1.paragraphs[0]
p1.text = "MERIDIAN MANUFACTURING LTD."
p1.font.size = Pt(16)
p1.font.bold = True
p1.font.color.rgb = TEAL

p2 = tf1.add_paragraph()
p2.text = "ERP-to-Analytics Production Integration Defence"
p2.font.size = Pt(32)
p2.font.bold = True
p2.font.color.rgb = NAVY

p3 = tf1.add_paragraph()
p3.text = "Mission-Critical SAP S/4HANA (2023 FPS02) to Zetheta FinSight 4.2 Financial Pipeline"
p3.font.size = Pt(16)
p3.font.color.rgb = SLATE

p4 = tf1.add_paragraph()
p4.text = "\nCandidate Reference ID: 493560B | Lead Forward Deployed Engineer (FDE-9B)\nClient Stakeholders: Ananya Krishnan (CFO) | Rajesh Venkataraman (VP IT) | Priya Deshmukh (SAP Basis) | Marcus Wei (Platform)\nClassification: Enterprise Production Baseline | October 2026"
p4.font.size = Pt(11)
p4.font.color.rgb = CHARCOAL

# Slide 2: Executive Context & Problem Statement
s2 = prs.slides.add_slide(slide_layout)
set_slide_bg(s2)
add_header(s2, "Executive Problem Statement & Legacy Architecture Pain Points")
add_card(s2, 0.8, 1.6, 3.6, 5.0, "Enterprise Scale & Footprint", [
    "Annual Revenue: INR 2,400 Crore",
    "7 Operating Plants across 3 States (MH, GJ, TN)",
    "Engine & Powertrain (Chakan 1100)",
    "Sheet Metal Pressing (Bhosari 1200)",
    "EV Systems & Chassis (Sanand 1300)",
    "Heavy Fabrication (Halol 1400)",
    "CV Assembly (Sriperumbudur 1500)",
    "R&D Test Track (Oragadam 1600)",
    "Precision Tooling (Hosur 1700)"
])
add_card(s2, 4.8, 1.6, 3.6, 5.0, "Legacy Integration Bottlenecks", [
    "24-Hour Latency: Nightly batch extracts created 1-day stale analytical reports",
    "6-Day Book Close: Finance team took 6 business days every month to close books",
    "Working Capital Blindspots: Delayed visibility into INR 450+ Cr open AP/AR invoices",
    "Manual Balancing: Reliance on Excel reconciliations causing audit break risks",
    "RFC Resource Conflicts: Uncoordinated extracts clashing with nightly jobs (RGGBS000)"
], border_color=GOLD, header_color=GOLD)
add_card(s2, 8.8, 1.6, 3.6, 5.0, "Production Imperatives", [
    "98% Latency Reduction (24 hours to < 30 mins)",
    "Zero-Break Balance Tolerance (+/- 0.00 INR)",
    "Network Guardrail: Strict 25% (112.5 Mbps) cap on 450 Mbps shared MPLS link",
    "SAP RFC Safeguard: Hard ceiling of 50 concurrent connections",
    "100% Indian Statutory Data Compliance (Companies Act 2013 & RBI localization)"
], border_color=TEAL, header_color=TEAL)

# Slide 3: Solution Architecture (4-Box Model)
s3 = prs.slides.add_slide(slide_layout)
set_slide_bg(s3)
add_header(s3, "Enterprise Solution Architecture: 4-Box Integration Model")
add_card(s3, 0.8, 1.6, 2.7, 5.0, "1. Source: SAP S/4HANA", [
    "On-Premise Pune Data Centre",
    "2023 FPS02 Release",
    "Custom CDS Views (ZCDS_*)",
    "Operational Data Provisioning (ODP)",
    "Universal Journal (ACDOCA)",
    "Sub-Ledgers (BSEG, BSIK, BSID)",
    "50 Max Concurrent RFC Leases",
    "Blackout: 01:00-04:30 IST"
])
add_card(s3, 3.8, 1.6, 2.7, 5.0, "2. Secure Network Highway", [
    "450 Mbps Shared MPLS Link",
    "SD-WAN Traffic Shaping",
    "Hard Cap: 25% (112.5 Mbps)",
    "IPsec Site-to-Site Tunnel",
    "TLS 1.3 Forward Secrecy",
    "AES-256 Wire Encryption",
    "Round-Trip Latency: 22-26ms",
    "Active Alerting at 100 Mbps"
], border_color=TEAL, header_color=TEAL)
add_card(s3, 6.8, 1.6, 2.7, 5.0, "3. Streaming Engine", [
    "Apache Kafka Cluster (3 Brokers)",
    "Kubernetes Microservices",
    "V3 Indian Fiscal Calendar Logic",
    "7-Level Hierarchy Flattener",
    "25 Automated DQ Rules",
    "Dual-Entry Balance Reconciler",
    "3-State Circuit Breaker",
    "14-Day S3 KMS Dead Letter Queue"
], border_color=NAVY, header_color=NAVY)
add_card(s3, 9.8, 1.6, 2.7, 5.0, "4. Target: FinSight 4.2", [
    "AWS Mumbai (ap-south-1)",
    "RESTful API (OpenAPI 3.0.3)",
    "mTLS + OAuth 2.0 Auth",
    "PostgreSQL RDS Analytical DW",
    "Schedule III Financial Reports",
    "Real-Time Working Capital",
    "7-Year Statutory Audit Store",
    "P95 Latency < 5.0s SLA"
], border_color=RGBColor(5, 150, 105), header_color=RGBColor(5, 150, 105))

# Slide 4: Business Value & Financial ROI
s4 = prs.slides.add_slide(slide_layout)
set_slide_bg(s4)
add_header(s4, "Quantified Commercial Impact & Financial ROI for Meridian")
add_card(s4, 0.8, 1.6, 3.6, 5.0, "Data Freshness: 98% Gain", [
    "Previous State: 24-hour delayed batch data",
    "Target State: < 30-minute continuous sync",
    "Real-time operational cash position",
    "Immediate insight into factory overheads",
    "Intra-day tracking of scrap and production variances across all 7 plants"
])
add_card(s4, 4.8, 1.6, 3.6, 5.0, "Accelerated Book Close", [
    "Previous State: Day +6 monthly financial close",
    "Target State: Day +2 certified close",
    "Saves 4 business days per fiscal month",
    "Frees ~450 finance team hours monthly",
    "Enables faster reporting to Board & Auditors",
    "Automates Schedule III balance sheet preparation"
], border_color=TEAL, header_color=TEAL)
add_card(s4, 8.8, 1.6, 3.6, 5.0, "Working Capital Optimization", [
    "Real-time tracking of INR 450+ Cr AP/AR",
    "Eliminates early payment penalties",
    "Maximizes MSME prompt payment discounts",
    "Optimizes short-term credit utilization",
    "Estimated Financial Savings: INR 1.8 to 2.4 Crore annually in working capital financing costs"
], border_color=GOLD, header_color=GOLD)

# Slide 5: Deliverable D1 - Integration Architecture
s5 = prs.slides.add_slide(slide_layout)
set_slide_bg(s5)
add_header(s5, "Deliverable D1: Integration Architecture & Hybrid Cloud Networking")
add_card(s5, 0.8, 1.6, 5.6, 5.0, "Network & Infrastructure Safeguards", [
    "Network Topology: On-Premise Pune DC (10.140.10.0/24) to AWS ap-south-1 (172.24.10.0/24)",
    "Bandwidth Enforcement: 112.5 Mbps hard limit enforced by SD-WAN token bucket shaper",
    "Connection Pooling: 50 RFC connections dedicated to Z_FINSIGHT_SVC via Redis semaphore",
    "Blackout Enforcement: Nightly job RGGBS000 (01:00 - 04:30 IST) protected via CRON fencing",
    "Kafka Partitioning: 12 partitions on raw topics for linear consumer load balancing"
])
add_card(s5, 6.8, 1.6, 5.6, 5.0, "Enterprise Security & Protocol Standards", [
    "Mutual TLS (mTLS): Dual-ended x509 cryptographic handshake with AWS ACM-PCA",
    "OAuth 2.0 Client Credentials Grant: JWT tokens with granular scopes (finsight.gl.write)",
    "Statutory Localization: 100% data residency maintained in AWS Asia Pacific (Mumbai)",
    "Data At-Rest: AES-256 Customer-Managed Keys (KMS CMK) across EBS, S3, and RDS",
    "Audit Immutability: S3 Compliance Object Lock preventing document tampering for 7 years"
], border_color=TEAL, header_color=TEAL)

# Slide 6: Deliverable D2 - API Specification
s6 = prs.slides.add_slide(slide_layout)
set_slide_bg(s6)
add_header(s6, "Deliverable D2: API Specification Document & OpenAPI 3.0.3 Contract")
add_card(s6, 0.8, 1.6, 5.6, 5.0, "API Architecture Standards", [
    "Specification Compliance: Strictly valid OpenAPI 3.0.3 passing Spectral with 0 errors",
    "Endpoint Orientation: RESTful resource hierarchy (/api/v2/ledger, /api/v2/recon)",
    "Payload Protocol: JSON over HTTP/2 with gzip stream compression (78% wire reduction)",
    "Idempotency Key Engine: Atomic Redis SETNX deduplication using document hash (72h TTL)",
    "Rate Limiting Contract: RFC 6585 HTTP 429 with explicit Retry-After headers"
])
add_card(s6, 6.8, 1.6, 5.6, 5.0, "Core API Endpoints & Interfaces", [
    "POST /api/v2/ledger/batch: Micro-batch ingestion (500 records/batch sweet spot)",
    "POST /api/v2/ap/open-items: Accounts payable aging and supplier invoice sync",
    "GET /api/v2/recon/reports/{batch_id}: Automated batch reconciliation certification report",
    "GET /api/v2/dlq/messages: Quarantine backlog inspection and error classification",
    "POST /api/v2/dlq/replay: Idempotent operational replay with audited justification"
], border_color=TEAL, header_color=TEAL)

# Slide 7: Deliverable D3 - Data Transformation
s7 = prs.slides.add_slide(slide_layout)
set_slide_bg(s7)
add_header(s7, "Deliverable D3: Data Transformation & Master Mapping Specification")
add_card(s7, 0.8, 1.6, 5.6, 5.0, "54 Field Mappings Across 10 Business Domains", [
    "Domain 1: General Ledger & Universal Journal (ACDOCA, BKPF) - 6 Mappings",
    "Domain 2: Accounts Payable & Vendor Master (BSEG, BSIK, LFA1, LFC1) - 6 Mappings",
    "Domain 3: Accounts Receivable & Customers (BSID, BSAD, KNA1) - 5 Mappings",
    "Domain 4: Cost Center Accounting & Controlling (CSKS, CSKT, SETNODE) - 6 Mappings",
    "Domain 5: Profit Center Accounting (CEPC, CEPCT) - 5 Mappings",
    "Domain 6: Procurement & Materials Management (EKKO, EKPO, MSEG) - 6 Mappings",
    "Domain 7: Sales & Distribution (VBAK, VBAP) - 5 Mappings",
    "Domain 8: Fixed Asset Accounting (ANLA, ANLP) - 5 Mappings",
    "Domain 9: Cash Management & Bank Statements (FEBKO, FEBEP) - 5 Mappings",
    "Domain 10: Currency Exchange & Treasury Rates (TCURR) - 5 Mappings"
])
add_card(s7, 6.8, 1.6, 5.6, 5.0, "Complex Statutory Business Logic Solved", [
    "Indian Fiscal Variant V3: Mapping April 1 to March 31 with special closing periods 13-16",
    "Schedule III Chart of Accounts: Normalizing SAP 10-digit GL accounts into statutory items",
    "GST 3-Way Tax Split: Resolving intra-state (CGST+SGST) vs inter-state (IGST) line splits",
    "7-Level Cost Center Hierarchy Flattening: Materializing recursive SETNODE/SETLEAF trees",
    "TCURR Currency Inversion: Handling indirect EUR/USD rates and triangulation to INR",
    "Fixed-Point Precision: Strict Decimal(18,2) avoiding IEEE 754 floating point drift"
], border_color=TEAL, header_color=TEAL)

# Slide 8: Deliverable D4 - Error Handling & Resiliency
s8 = prs.slides.add_slide(slide_layout)
set_slide_bg(s8)
add_header(s8, "Deliverable D4: Error Handling, Retry & Circuit Breaker Framework")
add_card(s8, 0.8, 1.6, 3.6, 5.0, "4-Class Error Taxonomy", [
    "TRANSIENT: Network glitches, 429/503 throttles -> Exponential backoff with jitter",
    "PERMANENT: Schema drift, 400/401/403 errors -> Immediate halt & DLQ quarantine",
    "DATA QUALITY: Unbalanced GL, bad GSTIN/PAN -> Isolated to S3 DLQ; stream continues",
    "SYSTEM: Node OOM, Kafka partition down -> Circuit breaker trip, P1 SRE alert"
])
add_card(s8, 4.8, 1.6, 3.6, 5.0, "Decorrelated Jitter Backoff", [
    "Formula: wait = min(cap, random(base, base * 2^attempt))",
    "Base = 2.0s | Multiplier = 2 | Cap = 60s",
    "Attempt 1: [2.0s, 4.0s] (mean 3.0s)",
    "Attempt 2: [2.0s, 8.0s] (mean 5.0s)",
    "Attempt 3: [2.0s, 16.0s] (mean 9.0s)",
    "Attempt 4: [2.0s, 32.0s] (mean 17.0s)",
    "Prevents thundering herd on SAP Gateway"
], border_color=TEAL, header_color=TEAL)
add_card(s8, 8.8, 1.6, 3.6, 5.0, "Circuit Breaker & DLQ", [
    "State Machine: CLOSED (0) -> OPEN (1) -> HALF-OPEN (2)",
    "Trip Condition: >=50% failures over 100 requests",
    "Reset Cooldown: 60 seconds fail-fast",
    "Half-Open Probe: 10 requests; requires >=90% success to close",
    "S3 DLQ Retention: 14 days in S3 Standard; 7 years in Glacier for audit compliance",
    "Replay Engine: REST API with idempotency"
], border_color=GOLD, header_color=GOLD)

# Slide 9: Deliverable D5 - Reconciliation & Data Quality
s9 = prs.slides.add_slide(slide_layout)
set_slide_bg(s9)
add_header(s9, "Deliverable D5: Reconciliation Logic & Data Quality Framework")
add_card(s9, 0.8, 1.6, 5.6, 5.0, "Four Dimensions of Financial Reconciliation", [
    "Completeness: Extracted = Loaded + Duplicates_Skipped + DLQ_Quarantined (0 count variance)",
    "Accuracy: Zero-Break Tolerance: Sum(Debits) - Sum(Credits) == 0.00 INR exactly",
    "Rounding Standard: Banker's Rounding (IEEE 754 Round Half Even) applied at line-item level",
    "Timeliness: End-to-end sync latency <= 30.0 minutes from SAP posting to FinSight",
    "Consistency: Cryptographic SHA-256 batch hash parity (Source Hash == Loaded Hash)"
])
add_card(s9, 6.8, 1.6, 5.6, 5.0, "25 Production Data Quality Rules", [
    "Null Checks (DQ-001..004): Document number, Plant code, Posting date, GL account",
    "Format Validation (DQ-005..008): GSTIN Luhn mod-36, PAN structure, V3 Fiscal, Currency",
    "Range Checks (DQ-009..012): Posting amount, TCURR exchange rate, Fiscal periods 01-16",
    "Referential Integrity (DQ-013..016): Active CSKS Cost Center, CEPC Profit Center, LFA1",
    "Cross-Field Checks (DQ-017..020): Plant-to-GSTIN state match, 3-way tax split equality",
    "Business Invariants (DQ-021..025): Dual-entry balance (0.00), High-water mark monotonicity"
], border_color=TEAL, header_color=TEAL)

# Slide 10: Deliverable D6 - Observability & Alerting
s10 = prs.slides.add_slide(slide_layout)
set_slide_bg(s10)
add_header(s10, "Deliverable D6: Monitoring Cockpit, Structured Logging & Alerting")
add_card(s10, 0.8, 1.6, 3.6, 5.0, "12-Panel Grafana Dashboard", [
    "MON-001: Pipeline Health Overview (Stat)",
    "MON-002: E2E Throughput (Records/Sec)",
    "MON-003: Processing Latency (P50/P95/P99)",
    "MON-004: Error Rate % by Error Class",
    "MON-005: DLQ Backlog Depth (Gauge)",
    "MON-006: Daily Financial Recon Break (0.00 INR)",
    "MON-007: SAP RFC Pool Utilization (out of 50)",
    "MON-008: FinSight Ingestion API Health",
    "MON-009: Data Freshness SLA Tracker (<30m)",
    "MON-010: Compute & Network Saturation",
    "MON-011: Kafka Consumer Group Lag",
    "MON-012: Circuit Breaker State Status"
])
add_card(s10, 4.8, 1.6, 3.6, 5.0, "Structured JSON Logging", [
    "12 Mandatory Attributes on Stdout",
    "timestamp (ISO-8601 UTC ms)",
    "correlation_id (UUIDv4 propagated)",
    "batch_id (Batch run identifier)",
    "plant_id (SAP Plant 1100..1700)",
    "sap_document_id (BELNR)",
    "log_level (INFO, WARN, ERROR, FATAL)",
    "component (extractor, transformer, etc.)",
    "duration_ms & records_processed",
    "error_code & error_class",
    "payload_checksum (SHA-256)"
], border_color=TEAL, header_color=TEAL)
add_card(s10, 8.8, 1.6, 3.6, 5.0, "15 Enterprise Alerting Rules", [
    "ALT-001: Financial Recon Zero-Break (P1 - Instant)",
    "ALT-002: RFC Pool Exhaustion >=45 (P2 - 1m)",
    "ALT-003: Circuit Breaker OPEN (P1 - 30s)",
    "ALT-004: Kafka Consumer Lag >25K (P2 - 5m)",
    "ALT-005: DLQ Quarantine Inflow Surge (P2 - 3m)",
    "ALT-006: Data Freshness SLA Breach >30m (P1)",
    "ALT-007: API 429 Throttle Rate >2/s (P3 - 1m)",
    "ALT-008: MPLS Bandwidth >100 Mbps (P2 - 2m)",
    "ALT-009: Nightly Job Window Collision (P2)",
    "ALT-010 to ALT-015: Memory, Tracing, Auth, Locks",
    "Automated Mitigation Runbooks (RB-FIN, RB-RFC)"
], border_color=GOLD, header_color=GOLD)

# Slide 11: Deliverable D7 - Integration Test Plan
s11 = prs.slides.add_slide(slide_layout)
set_slide_bg(s11)
add_header(s11, "Deliverable D7: Integration Testing Plan (25 Scenarios Executed)")
add_card(s11, 0.8, 1.6, 5.6, 5.0, "Test Scenarios Coverage Breakdown", [
    "10 Functional Tests (TST-FNC-001..010): GL Happy Path, AP Aging, Cost Center Sync, Multi-Company Code (MC01-03), Fiscal V3, 7-Level Tree, P2P Trace, Bank Statement Recon, Budget Actuals, End-of-Day Zero Break.",
    "5 Performance Tests (TST-NFR-001..005): 500K records in 74 min (vs <120m SLA), 12 concurrent streams (38/50 RFCs), P95 latency 3.22s (<5s SLA), Linear scalability (R2 >= 0.985), 24h endurance leak test.",
    "5 Failure Injection Tests (TST-FLR-001..005): RFC socket kill (resumed w/o duplicates), 429 throttling backoff, Kafka broker abrupt crash, Malformed poison pill DLQ isolation, 5-minute MPLS severance.",
    "3 Security Tests (TST-SEC-001..003): OAuth token silent refresh at T-60s, 401/403 audit logging, TLS 1.3 & AES-256 KMS cipher verification.",
    "2 Reconciliation Tests (TST-REC-001..002): Deliberate INR 1.50 checksum break (instant batch halt), Orphaned Cost Center quarantine."
])
add_card(s11, 6.8, 1.6, 5.6, 5.0, "Verified Test Execution Results", [
    "Total Test Cases: 25 / 25 Passed (100% Pass Rate)",
    "Peak Batch Throughput: 112 records/sec sustained",
    "Peak MPLS Bandwidth: 82.4 Mbps (Under 112.5 Mbps cap)",
    "Peak RFC Connections: 38 (Under 50 connection ceiling)",
    "Worker Memory Drift: <5% over 24-hour non-stop load",
    "Data Loss Rate: Exactly 0 records lost across all failure tests",
    "Financial Discrepancy Break: 0.00 INR confirmed",
    "Security Vulnerabilities: Zero high/medium findings"
], border_color=TEAL, header_color=TEAL)

# Slide 12: Deliverable D8 - Deployment Runbook & Rollback
s12 = prs.slides.add_slide(slide_layout)
set_slide_bg(s12)
add_header(s12, "Deliverable D8: Deployment Runbook & Emergency Rollback Safeguards")
add_card(s12, 0.8, 1.6, 5.6, 5.0, "Cutover Execution Timeline (T-6h to T+2h)", [
    "T-360m: Bridge Convened & 15 Pre-Deployment Gates Verified",
    "T-180m: Non-essential background SAP jobs frozen",
    "T-60m: Baseline SAP ODP delta pointers and high-water marks captured",
    "T-00m: Production Kafka topics provisioned (3x replication, 14d retention)",
    "T+10m: Helm upgrade deploying release v4.2.0-RELEASE across EKS",
    "T+20m: Redis master data cache seeded with Cost & Profit Centers",
    "T+30m: 10 Post-Deployment Smoke Verification Checks executed",
    "T+60m: Initial 30-minute delta sync executed across all 7 plants",
    "T+120m: Zero-break reconciliation certificate signed & CAB ticket closed"
])
add_card(s12, 6.8, 1.6, 5.6, 5.0, "Rollback Protocol & Decision Council", [
    "Decision Council: Rajesh Venkataraman (VP IT), Priya Deshmukh (Basis), FDE Lead",
    "Decision Window: Strict 15-minute maximum evaluation window",
    "Trigger Conditions: Recon break != 0.00 INR, Error rate > 5%, RFC pool > 48, MPLS link degradation",
    "Automated Rollback Script: Halts pipeline worker pods in < 15 seconds",
    "State Restoration: Reverts SAP ODP delta high-water mark to pre-cutover baseline snapshot",
    "Queue Purge: Safely drains and resets Kafka consumer group offsets",
    "Target Recovery Time: Under 8 minutes total rollback duration with 0 data loss"
], border_color=GOLD, header_color=GOLD)

# Slide 13: Operational Governance & Support Tiering
s13 = prs.slides.add_slide(slide_layout)
set_slide_bg(s13)
add_header(s13, "Operational Governance, Support Model & Runbook SLAs")
add_card(s13, 0.8, 1.6, 3.6, 5.0, "Tier 1: Service Desk (L1)", [
    "24/7 Meridian Global IT Helpdesk",
    "Monitors Grafana MON-001 Cockpit",
    "Initial triage of pipeline alerts",
    "Basic service restarts and health pings",
    "Ticket dispatch to L2 engineering",
    "Response SLA: < 15 minutes"
])
add_card(s13, 4.8, 1.6, 3.6, 5.0, "Tier 2: FDE / Integration (L2)", [
    "Zetheta Forward Deployed Engineers",
    "Kubernetes pod lifecycle & scaling",
    "Kafka consumer lag & rebalance triage",
    "DLQ quarantine review & replay execution",
    "Data Quality transformation updates",
    "Response SLA: < 30 minutes"
], border_color=TEAL, header_color=TEAL)
add_card(s13, 8.8, 1.6, 3.6, 5.0, "Tier 3: Platform & Basis (L3)", [
    "Priya Deshmukh (SAP Basis Lead)",
    "Marcus Wei (Principal Platform Architect)",
    "SAP RFC work process & lock contention",
    "MPLS BGP routing & SD-WAN shaper",
    "Financial reconciliation break forensic audits",
    "P1 Critical SLA: < 15 min response, < 2 hr resolution"
], border_color=NAVY, header_color=NAVY)

# Slide 14: Final Sign-off
s14 = prs.slides.add_slide(slide_layout)
set_slide_bg(s14)
add_header(s14, "Production Sign-Off & Go-Live Authorization")
add_card(s14, 0.8, 1.6, 11.6, 5.0, "Formal Stakeholder Attestation & Approvals", [
    "100% Deliverable Completion: All specifications D1 through D9 delivered, linted, and verified.",
    "25 Integration Test Scenarios: 100% passed with zero functional or security exceptions.",
    "Statutory Compliance Verified: Dual-entry zero-break tolerance (+/- 0.00 INR) certified.",
    "Infrastructure Guardrails Enforced: 112.5 Mbps MPLS bandwidth cap and 50 RFC connection pool hard ceiling operationalized.",
    "\nEXECUTIVE SIGN-OFF BLOCKS:\n",
    "Ananya Krishnan (Chief Financial Officer): ___________________________   Date: ____/____/2026",
    "Rajesh Venkataraman (VP IT):               ___________________________   Date: ____/____/2026",
    "Priya Deshmukh (SAP Basis Lead):          ___________________________   Date: ____/____/2026",
    "Lead Forward Deployed Engineer (Zetheta): ___________________________   Date: ____/____/2026"
], border_color=TEAL, header_color=NAVY)

pptx_path_named = os.path.join(pres_dir, "493560B_LeadEngineer_Presentation.pptx")
pptx_path_generic = os.path.join(pres_dir, "493560B_[YourName]_Presentation.pptx")
prs.save(pptx_path_named)
prs.save(pptx_path_generic)
print(f"Successfully generated 14-slide presentation deck at {pptx_path_named} and {pptx_path_generic}!")
