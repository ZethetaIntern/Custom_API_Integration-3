# MERIDIAN MANUFACTURING LTD. | PRODUCTION INTEGRATION BLUEPRINT
**Document Reference:** ZET-MM-D7-TEST-2026-V1  
**Project:** Meridian ERP-to-Analytics Integration (SAP S/4HANA to FinSight 4.2)  
**Classification:** Confidential / Enterprise Production Standard  
**Revision Date:** October 2026  
**Status:** Approved for Production Deployment  

---
# MODULE 1: DELIVERABLE D7 - INTEGRATION TESTING PLAN (25 SCENARIOS)

## 1.1 TESTING GOVERNANCE & TEST HARNESS ARCHITECTURE

The integration test suite validates the end-to-end data pipeline from SAP S/4HANA (Pune On-Premises) through the Kafka streaming integration layer to Zetheta FinSight 4.2 (AWS ap-south-1). The test framework uses automated PyTest harnesses, Locust load-generation clusters, Chaos Mesh failure injectors, and cryptographic ledger verification checkers.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           INTEGRATION TEST HARNESS                               │
├─────────────────────────┬──────────────────────────┬─────────────────────────────┤
│   Functional Testing    │  Performance & Scale     │   Chaos & Security          │
│   • 10 Business Cases   │  • Locust Load Engine    │   • Chaos Mesh (MPLS / Net) │
│   • Multi-Company Code  │  • 500K Batch Engine     │   • OAuth Attack Simulators │
│   • Schedule III Audit  │  • 12 Concurrent Streams │   • Cryptographic Checksum  │
└─────────────────────────┴──────────────────────────┴─────────────────────────────┘
```

---

## 1.2 COMPLETE 25 TEST SCENARIOS MATRIX

### CATEGORY 1: FUNCTIONAL TEST SCENARIOS (10 TESTS: TST-FNC-001 TO TST-FNC-010)

#### TST-FNC-001: General Ledger Happy Path Extraction
* **Category:** Functional (GL Core)
* **Objective:** Verify end-to-end extraction, transformation, and ingestion of standard dual-entry General Ledger postings from SAP table `ACDOCA` to FinSight `GL_TRANSACTIONS`.
* **Preconditions:** SAP S/4HANA test client 100 loaded with 50 posted GL journals in Company Code `1000`. Delta high-water mark initialized.
* **Step-by-Step Execution:**
  1. Post journal batch via SAP transaction `FB50` (50 documents, 100 line items, balance = 0.00 INR).
  2. Trigger scheduled ODP delta extractor: `POST /api/v1/extractor/delta/trigger?source=ZCDS_ACDOCA_DELTA`.
  3. Inspect Kafka topic `meridian.sap.acdoca.raw.v1` for 100 incoming Avro records.
  4. Allow transformation worker to map Indian Fiscal Variant V3 and Chart of Accounts.
  5. Ingest into FinSight via `POST /api/v2/ledger/batch`.
  6. Query FinSight analytical database: `SELECT COUNT(*), SUM(debit_amount_inr) - SUM(credit_amount_inr) FROM finsight_dw.gl_postings WHERE batch_id = 'TST-001'`.
* **Expected Result:** Exactly 100 line items ingested. Duration $< 45\text{ seconds}$. Net balance variance equals exactly $0.00\text{ INR}$. Checksum verification passes.
* **Pass/Fail Criteria:** PASS if 100 records committed with zero balance break. FAIL if count mismatch, field truncation, or net balance $\ne 0.00\text{ INR}$.

#### TST-FNC-002: Accounts Payable Open Item Aging Analysis
* **Category:** Functional (AP Sub-Ledger)
* **Objective:** Validate open vendor invoices (`BSIK`), cleared invoices (`BSAK`), and vendor master (`LFA1`) synchronization for AP aging buckets (0-30, 31-60, 61-90, 90+ days).
* **Preconditions:** Vendor accounts populated with overdue open items across Pune Chakan (Plant 1100) and Hosur (Plant 1700).
* **Step-by-Step Execution:**
  1. Extract 2,000 open item records from `BSIK` with posting dates ranging across past 120 days.
  2. Transform baseline dates (`ZFBDT`) and calculate payment terms (`ZTERM`).
  3. Stream to FinSight AP Analytics endpoint `POST /api/v2/ap/open-items`.
  4. Compare FinSight calculated aging bucket totals against SAP standard report `S_ALR_87012085`.
* **Expected Result:** Aging bucket assignments match SAP report with zero rupee variance across all 4 aging tranches.
* **Pass/Fail Criteria:** PASS if line-item aging days and bucket sums match SAP report to the exact rupee.

#### TST-FNC-003: Cost Centre Master Hierarchy Sync
* **Category:** Functional (Controlling - Master Data)
* **Objective:** Verify synchronization and local Redis cache warm-up of active Cost Centres (`CSKS`) and texts (`CSKT`) across Controlling Area `IN01`.
* **Preconditions:** Redis cluster operational; 450 Cost Centres active in SAP S/4HANA.
* **Step-by-Step Execution:**
  1. Trigger master data sync job `sync_master_cost_centers`.
  2. Query Redis master data cache: `KEYS cc:IN01:*`.
  3. Add new cost centre `CC1300-EV-RND` in SAP via `KS01`.
  4. Trigger delta sync and query cache.
* **Expected Result:** Initial 450 records cached. Delta run detects and caches `CC1300-EV-RND` within 120 seconds with valid hierarchy node link.
* **Pass/Fail Criteria:** PASS if cache hit ratio is $100\%$ on subsequent document transformations.

#### TST-FNC-004: Multi-Company-Code Batching (MC01, MC02, MC03)
* **Category:** Functional (Multi-Entity Batching)
* **Objective:** Ensure single batch accurately partitions transactions across three legal entities: Meridian Manufacturing Ltd. (`MC01`), Meridian Precision Tooling (`MC02`), and Meridian EV Systems (`MC03`).
* **Preconditions:** Inter-company postings prepared with clearing accounts `299000` active.
* **Step-by-Step Execution:**
  1. Ingest synthetic batch containing 3,000 records (1,000 per company code) including 150 inter-company cross-charges.
  2. Process batch through partitioning transformer.
  3. Verify FinSight API segregates tenancy by `company_code`.
* **Expected Result:** 3 partitioned tenant sub-batches created. Inter-company clearing lines balance within each respective legal entity.
* **Pass/Fail Criteria:** PASS if entity tenant segregation maintains $100\%$ data isolation and separate reconciliation certificates pass.

#### TST-FNC-005: Indian Fiscal Period Mapping (Variant V3)
* **Category:** Functional (Statutory Calendar)
* **Objective:** Verify SAP Fiscal Variant V3 (April 1 to March 31) conversion to FinSight standard periods, including special audit closing periods 13-16.
* **Preconditions:** Test journal entries prepared for April 15, 2026 (Period 01), January 10, 2027 (Period 10), and March 31, 2027 Special Audit Run (Period 13).
* **Step-by-Step Execution:**
  1. Pass transactions through date transformer function `map_v3_fiscal_period()`.
  2. Assert generated fields: `fiscal_year`, `fiscal_period`, `is_special_period`.
* **Expected Result:**
  * April 15, 2026 -> Fiscal Year `2026`, Period `01`, `is_special_period=false`.
  * Jan 10, 2027 -> Fiscal Year `2026`, Period `10`, `is_special_period=false`.
  * Mar 31, 2027 (Period 13) -> Fiscal Year `2026`, Period `13`, `is_special_period=true`.
* **Pass/Fail Criteria:** PASS if all 3 variants evaluate with zero mapping errors.

#### TST-FNC-006: 7-Level Cost Centre Hierarchy Flattening
* **Category:** Functional (Controlling & Aggregation)
* **Objective:** Validate flattening of recursive 7-level SAP standard hierarchy (`SETNODE`/`SETLEAF`) into dimensional columns (`L1_CORP`, `L2_REGION`, `L3_PLANT`, `L4_DIVISION`, `L5_DEPT`, `L6_SECTION`, `L7_COSTCENTER`).
* **Preconditions:** Full hierarchy tree exported from SAP KSH3 for Plant 1100 (Chakan Powertrain).
* **Step-by-Step Execution:**
  1. Stream cost centre transaction for `CC1100-ENG-BLOCK-LINE2`.
  2. Execute flattening transformer using materialized hierarchy graph.
  3. Assert dimensional attributes populated in FinSight target schema.
* **Expected Result:** All 7 levels correctly resolved from root `CORP-MERIDIAN` down to leaf without null intermediate nodes.
* **Pass/Fail Criteria:** PASS if transformed row contains identical hierarchy path to SAP Controlling reports.

#### TST-FNC-007: Procure-to-Pay (P2P) End-to-End Tracing
* **Category:** Functional (Cross-Module Integration)
* **Objective:** Validate end-to-end document chain linking: Purchase Order (`EKKO`/`EKPO`) -> Goods Receipt (`MKPF`/`MSEG`) -> Invoice Receipt (`BKPF`/`BSEG`) -> Bank Payment Clearing (`BSAK`/`FEBEP`).
* **Preconditions:** P2P transaction cycle executed in SAP for INR 1,250,000.00 casting equipment purchase.
* **Step-by-Step Execution:**
  1. Trigger extractors across MM, FI, and Banking CDS views.
  2. Join records on Purchase Order Number (`EBELN`) and Reference Document (`XBLNR`).
  3. Ingest unified graph into FinSight P2P Analytics model.
* **Expected Result:** Single unified trace ID generated. Quantitative reconciliation confirms PO Qty = GR Qty = IR Qty (10 units). Total amount equals INR 1,250,000.00.
* **Pass/Fail Criteria:** PASS if all document links resolve with zero orphaned references.

#### TST-FNC-008: Electronic Bank Statement Reconciliation
* **Category:** Functional (Cash & Treasury)
* **Objective:** Verify automated parsing of MT940/CAMT.053 Electronic Bank Statements (`FEBKO`/`FEBEP`) against open GL clearing accounts.
* **Preconditions:** HDFC Bank clearing account `0000110001` with 150 unsettled RTGS vendor disbursement entries.
* **Step-by-Step Execution:**
  1. Ingest electronic bank statement feed containing 150 cleared transaction lines.
  2. Execute automated reconciliation matcher against open payment vouchers.
  3. Compute unallocated variance.
* **Expected Result:** 148 items matched automatically via UTR reference numbers. 2 unmatched items routed to Treasury review queue with net clearing variance = 0.00 INR.
* **Pass/Fail Criteria:** PASS if matched transactions flag as CLEARED in FinSight with zero GL balance discrepancy.

#### TST-FNC-009: Budget vs. Actual Variance Verification
* **Category:** Functional (Management Accounting)
* **Objective:** Validate commitment and actual cost aggregation against planned annual budgets (`COSP`/`COSS`) for Plant 1500 (Sriperumbudur).
* **Preconditions:** FY2026 approved OPEX budget loaded in FinSight budget tables.
* **Step-by-Step Execution:**
  1. Ingest monthly actuals batch totaling INR 18.5 Crore across Sriperumbudur cost centers.
  2. Compute variance: $\text{Variance} = \text{Budget} - \text{Actual}$.
  3. Validate threshold alerting on departments exceeding $90\%$ budget utilization.
* **Expected Result:** Aggregated actuals match SAP report `S_ALR_87013611` to the exact rupee. Automated notification triggered for Plant 1500 Assembly Line 2.
* **Pass/Fail Criteria:** PASS if variance values match SAP standard reports with $0.00\text{ INR}$ deviation.

#### TST-FNC-010: End-of-Day Zero-Break Balance Reconciliation
* **Category:** Functional (Reconciliation)
* **Objective:** Execute full batch reconciliation audit across all 7 plants at close of business.
* **Preconditions:** All business hour delta batches committed. Daily total transactions = 142,500 records.
* **Step-by-Step Execution:**
  1. Trigger End-of-Day reconciliation worker: `POST /api/v1/recon/eod-audit`.
  2. Reconcile total debits vs total credits for all 7 company plants.
  3. Verify equation: $Extracted = Loaded + Duplicates + Quarantined$.
* **Expected Result:**
  * Total Debits: `INR 4,825,910,240.50`
  * Total Credits: `INR 4,825,910,240.50`
  * Variance: `0.0000 INR`
  * Status: `ZERO_BREAK_CONFIRMED`.
* **Pass/Fail Criteria:** PASS only if financial variance is exactly $\pm 0.00\text{ INR}$ across all plants.

---

### CATEGORY 2: NON-FUNCTIONAL / PERFORMANCE SCENARIOS (5 TESTS: TST-NFR-001 TO TST-NFR-005)

#### TST-NFR-001: Peak Load Batch Processing (500K Records in < 2 Hours)
* **Category:** Performance (Throughput)
* **Objective:** Prove system ingests, validates, and stores a month-end peak volume of 500,000 SAP records in $< 120\text{ minutes}$ ($> 70\text{ records/sec}$ sustained) without exceeding 112.5 Mbps MPLS bandwidth cap.
* **Preconditions:** Locust load injection cluster deployed on AWS; SAP mock provider pre-loaded with 500K `ACDOCA` records.
* **Step-by-Step Execution:**
  1. Start extraction workers with concurrency = 8.
  2. Monitor Prometheus metric `rate(pipeline_records_processed_total[1m])`.
  3. Monitor network egress rate: `rate(container_network_transmit_bytes_total[1m]) * 8 / 1000000`.
  4. Track elapsed time from batch start to final database commit.
* **Expected Result:** Total processing time: **74 minutes 18 seconds** (average 112 records/sec). Peak bandwidth utilization: **82.4 Mbps** (safely below 112.5 Mbps cap).
* **Pass/Fail Criteria:** PASS if 500K records fully processed in $< 120\text{ minutes}$ with zero records lost and bandwidth $< 112.5\text{ Mbps}$.

#### TST-NFR-002: Twelve (12) Concurrent Extraction Streams
* **Category:** Performance (Concurrency & Pool Contention)
* **Objective:** Ensure pipeline orchestrates 12 simultaneous extraction streams (7 plants + 5 master data domains) while respecting the 50 RFC connection ceiling.
* **Preconditions:** SAP RFC connection pool configured with `max_pool_size=50`.
* **Step-by-Step Execution:**
  1. Trigger simultaneous sync jobs for Plants 1100-1700 plus Vendor, Customer, Cost Centre, Profit Centre, and Exchange Rates.
  2. Poll RFC pool utilization metric: `sap_rfc_pool_active_connections`.
  3. Verify connection acquisition wait times and queue depth.
* **Expected Result:** Peak concurrent RFC connections reach **38 out of 50** ($76\%$). Zero connection timeouts or pool exhaustion exceptions.
* **Pass/Fail Criteria:** PASS if all 12 streams complete concurrently without any `ERR-EXT-001` errors and active RFC connections $\le 45$.

#### TST-NFR-003: FinSight API Ingestion Latency SLA Verification (P95 < 5s)
* **Category:** Performance (Latency SLA)
* **Objective:** Confirm FinSight API micro-batch ingestion latency meets contractual SLA: P50 $< 2.0\text{s}$, P95 $< 5.0\text{s}$, P99 $< 15.0\text{s}$ under steady-state load (500 records/batch).
* **Preconditions:** Ingestion endpoint under continuous load of 25 batch requests/sec.
* **Step-by-Step Execution:**
  1. Execute 10,000 HTTP POST batch ingestion calls over 30 minutes.
  2. Compute latency percentiles via Prometheus histogram:
     `histogram_quantile(0.95, sum(rate(http_client_request_duration_seconds_bucket[5m])) by (le))`.
* **Expected Result:** P50 = **1.14s**, P95 = **3.22s**, P99 = **6.81s**.
* **Pass/Fail Criteria:** PASS if P95 latency is strictly $< 5.0\text{ seconds}$ and zero HTTP 504 timeouts occur.

#### TST-NFR-004: Linear Scalability Benchmark (1K to 100K Records)
* **Category:** Performance (Scalability Profile)
* **Objective:** Demonstrate linear processing time scaling as batch size increases from 1,000 to 10,000 to 50,000 to 100,000 records.
* **Preconditions:** Synthetic batch generator configured for variable payload sizes.
* **Step-by-Step Execution:**
  1. Execute batches of 1K, 10K, 50K, and 100K records.
  2. Record end-to-end processing duration for each run.
  3. Plot regression curve and calculate scaling coefficient $R^2$.
* **Expected Result:**
  * 1K records: 12.4 seconds
  * 10K records: 98.2 seconds
  * 50K records: 472.0 seconds
  * 100K records: 924.5 seconds
  * Linear correlation coefficient $R^2 \ge 0.985$.
* **Pass/Fail Criteria:** PASS if scaling curve exhibits linear $O(N)$ characteristics without exponential degradation.

#### TST-NFR-005: 24-Hour Continuous Endurance & Memory Leak Test
* **Category:** Performance (Endurance & Stability)
* **Objective:** Validate memory stability, JVM garbage collection efficiency, and absence of file descriptor leaks across a 24-hour non-stop production simulation.
* **Preconditions:** Worker pods instrumented with Prometheus JVM/Go runtime exporters.
* **Step-by-Step Execution:**
  1. Run pipeline continuously for 24 hours under steady-state delta load (15,000 records every 30 minutes).
  2. Monitor container working set memory: `container_memory_working_set_bytes`.
  3. Inspect open file descriptors: `process_open_fds`.
* **Expected Result:** Memory working set stabilizes at **1.42 GB** ($57\%$ of 2.5 GB pod limit). Heap usage exhibits periodic saw-tooth pattern with full GC recovery. Zero memory leaks detected.
* **Pass/Fail Criteria:** PASS if worker pods experience zero OOM evictions, memory drift $< 5\%$ over final 12 hours, and zero dropped messages.

---

### CATEGORY 3: FAILURE INJECTION SCENARIOS (5 TESTS: TST-FLR-001 TO TST-FLR-005)

#### TST-FLR-001: SAP RFC Mid-Batch Connection Severance
* **Category:** Failure Injection (Source Disruption)
* **Objective:** Validate graceful recovery and zero data loss when SAP RFC socket is abruptly terminated midway through a 10,000-record extraction stream.
* **Preconditions:** Extraction batch actively in-flight at record 4,500.
* **Step-by-Step Execution:**
  1. Kill active RFC TCP socket on Pune gateway using `tcpkill -i eth0 port 3300`.
  2. Observe extractor handling: error classified as `TRANSIENT` (`ERR-EXT-001`).
  3. Verify decorrelated jitter backoff engages (Attempts 1-4).
  4. Restore network connectivity after 20 seconds.
* **Expected Result:** Extractor reconnects on Attempt 2 (wait ~5.2s), re-queries ODP delta high-water mark, resumes from uncommitted record 4,501, and finishes batch without duplicates.
* **Pass/Fail Criteria:** PASS if batch completes with 10,000 records committed, zero duplicates, and zero missing records.

#### TST-FLR-002: Destination API HTTP 429 Throttling Backoff Verification
* **Category:** Failure Injection (Target Rate Limiting)
* **Objective:** Verify client-side rate throttling and exponential backoff when FinSight Ingestion API returns HTTP 429 Too Many Requests with header `Retry-After: 15`.
* **Preconditions:** Mock FinSight API programmed to reject requests exceeding 10 req/sec with HTTP 429.
* **Step-by-Step Execution:**
  1. Burst traffic from 16 worker threads to trigger HTTP 429.
  2. Capture outgoing HTTP client logs and retry timestamps.
  3. Verify worker throttles concurrency down to 4 threads and sleeps for 15 seconds.
* **Expected Result:** Worker respects `Retry-After` header, enters backoff state without dropping payloads, and successfully flushes buffered batches upon cooldown.
* **Pass/Fail Criteria:** PASS if zero payloads are dropped to DLQ and client recovers automatically.

#### TST-FLR-003: Kafka Single Broker Abrupt Termination
* **Category:** Failure Injection (Infrastructure Fault)
* **Objective:** Confirm Kafka cluster tolerance and zero message loss when one broker out of three in AWS `ap-south-1` is terminated abruptly (`kill -9`).
* **Preconditions:** Kafka topic configured with `replication.factor=3`, `min.insync.replicas=2`, `acks=all`.
* **Step-by-Step Execution:**
  1. Stream continuous transactions at 250 records/sec.
  2. Terminate Kafka Broker 2 pod abruptly via `kubectl delete pod kafka-broker-2 --force --grace-period=0`.
  3. Monitor producer message delivery confirmations and consumer group partition rebalance.
* **Expected Result:** Cluster partitions re-elect leaders within 1.8 seconds. Producer observes transient retryable exceptions, retries automatically, and experiences zero message loss.
* **Pass/Fail Criteria:** PASS if 100% of messages are delivered (`acks=all`) and consumer lag normalizes within 60 seconds of pod recovery.

#### TST-FLR-004: Corrupted Malformed Payload Quarantine
* **Category:** Failure Injection (Data Corruption)
* **Objective:** Validate that a malformed JSON payload (invalid UTF-8 bytes and truncated closing brackets) is cleanly isolated to the S3 DLQ without stalling the consumer partition.
* **Preconditions:** DLQ S3 bucket and quarantine topic active.
* **Step-by-Step Execution:**
  1. Inject corrupted record into Kafka partition alongside 999 valid financial records.
  2. Transformation worker encounters JSON deserialization failure.
  3. Assert error classified as `PERMANENT` (`ERR-LOAD-004`).
  4. Verify corrupted message routed to S3 DLQ with full diagnostic envelope.
  5. Inspect consumer group offset: verify partition advances to record 1,001.
* **Expected Result:** 999 valid records committed to FinSight. 1 corrupted record written to `s3://meridian-prod-dlq-ap-south-1/quarantine/`. Pipeline consumer does not crash or loop.
* **Pass/Fail Criteria:** PASS if poison pill message is isolated in $< 500\text{ms}$ and remaining 999 records commit successfully.

#### TST-FLR-005: 5-Minute Simulated Network Partition Across MPLS Link
* **Category:** Failure Injection (Network Disruption)
* **Objective:** Test end-to-end resilience when the 450 Mbps MPLS link between Pune DC and AWS Mumbai suffers a total 5-minute outage.
* **Preconditions:** Chaos Mesh network partition rule configured.
* **Step-by-Step Execution:**
  1. Apply Chaos Mesh network drop rule simulating MPLS severed link.
  2. Observe on-premise extractor buffering records to local NVMe spillover storage.
  3. Verify circuit breaker trips from CLOSED to OPEN after 100 failed connection attempts.
  4. Restore MPLS network link after 5 minutes.
  5. Observe circuit breaker transition from OPEN to HALF-OPEN (canary probes), then CLOSED.
* **Expected Result:** During partition, zero records lost; local buffer holds 4,500 records. Upon reconnection, buffer drains at 95 Mbps, clearing backlog in 4.2 minutes.
* **Pass/Fail Criteria:** PASS if zero data lost, circuit breaker transitions correctly, and all buffered records commit with full reconciliation sign-off.

---

### CATEGORY 4: SECURITY & COMPLIANCE SCENARIOS (3 TESTS: TST-SEC-001 TO TST-SEC-003)

#### TST-SEC-001: OAuth 2.0 Token Expiration & Silent Auto-Refresh
* **Category:** Security (Authentication Lifecycle)
* **Objective:** Verify OAuth 2.0 JWT bearer token expiration is handled seamlessly via pre-emptive background token refresh without failing active batch ingestions.
* **Preconditions:** FinSight OAuth token configured with short 300-second TTL.
* **Step-by-Step Execution:**
  1. Initiate 1-hour continuous ingestion job.
  2. Track token cache refresh events in worker debug logs.
  3. Verify token refresh initiates at $T - 60\text{ seconds}$ (at 240 seconds).
* **Expected Result:** Client obtains new JWT token using mTLS client credentials before current token expires. Zero HTTP 401 Unauthorized errors observed during 12 refresh cycles.
* **Pass/Fail Criteria:** PASS if $100\%$ of batch calls succeed across token rollover boundaries.

#### TST-SEC-002: Unauthorized Access Rejection (401/403 Audit Logging)
* **Category:** Security (Authorization & Audit Compliance)
* **Objective:** Confirm pipeline rejects unauthorized access attempts (invalid JWT signature, expired mTLS certificate, or missing `finsight.gl.write` scope) and emits statutory security audit logs.
* **Preconditions:** Test service client configured with forged JWT token and revoked client certificate.
* **Step-by-Step Execution:**
  1. Attempt `POST /api/v2/ledger/batch` using invalid certificate.
  2. Attempt ingestion using valid cert but missing `finsight.gl.write` scope.
  3. Inspect CloudWatch and SIEM audit logs for security event emissions.
* **Expected Result:** Ingress gateway rejects calls with HTTP 401 and 403 respectively. Security log generated with IP address, certificate thumbprint, and timestamp.
* **Pass/Fail Criteria:** PASS if access is blocked immediately and security incident event is logged in SIEM within 5 seconds.

#### TST-SEC-003: In-Transit TLS 1.3 & At-Rest AES-256 Cipher Validation
* **Category:** Security (Cryptographic Compliance)
* **Objective:** Validate that all network communications strictly enforce TLS 1.3 with forward secrecy, and all storage volumes (EBS, S3, Kafka) use AES-256 KMS encryption.
* **Preconditions:** SSL test harness and AWS KMS auditing tools configured.
* **Step-by-Step Execution:**
  1. Scan all public and private endpoints with `testssl.sh`: verify TLS 1.0, 1.1, and 1.2 are rejected.
  2. Verify supported cipher suites: `TLS_AES_256_GCM_SHA384` and `TLS_CHACHA20_POLY1305_SHA256`.
  3. Inspect S3 bucket configuration: confirm `ServerSideEncryptionConfiguration` uses KMS CMK.
  4. Inspect EBS volume attributes: confirm `Encrypted: true`.
* **Expected Result:** Weak ciphers rejected. TLS 1.3 strictly enforced. S3 and EBS encrypted with Customer-Managed Key `arn:aws:kms:ap-south-1:112233445566:key/meridian-dlq-cmk`.
* **Pass/Fail Criteria:** PASS if zero cryptographic vulnerabilities detected and encryption is 100% active.

---

### CATEGORY 5: RECONCILIATION DISCREPANCY SCENARIOS (2 TESTS: TST-REC-001 TO TST-REC-002)

#### TST-REC-001: Injection of Deliberate INR 1.50 Checksum Break
* **Category:** Reconciliation (Financial Integrity Circuit Breaker)
* **Objective:** Prove that an in-flight corruption or rounding drift of just **INR 1.50** instantly trips the financial reconciliation circuit breaker, halts the batch, and triggers P1 alerting.
* **Preconditions:** Reconciler engine monitoring live batch processing.
* **Step-by-Step Execution:**
  1. Manually tamper with transformed line item #42: modify debit amount from `48,250.00` to `48,251.50 INR`.
  2. Transmit batch to ingestion engine.
  3. Reconciler executes dual-entry integrity check: $\sum\text{Debits} - \sum\text{Credits} = +1.50\text{ INR}$.
  4. Observe pipeline response: error classified as `ERR-RECON-001`.
* **Expected Result:** Batch commit is rejected. Automated runbook `RB-FIN-001` fires: worker pods scaled to 0, delta token high-water mark frozen, P1 alert dispatched to PagerDuty (`ALT-001`).
* **Pass/Fail Criteria:** PASS if pipeline halts immediately, zero corrupt data is permanently committed, and P1 incident fires within 2 seconds.

#### TST-REC-002: Orphaned Line Item Pointing to Non-Existent Cost Centre
* **Category:** Reconciliation (Referential Integrity Quarantine)
* **Objective:** Validate that a transaction referencing a deleted or unmapped Cost Centre (`CC9999-FAKE`) is quarantined without disrupting valid transactions in the same batch.
* **Preconditions:** Master data cache contains valid Cost Centres for Plants 1100-1700.
* **Step-by-Step Execution:**
  1. Ingest batch of 100 records where record #88 contains invalid `KOSTL = 'CC9999-FAKE'`.
  2. Referential integrity rule `DQ-013` executes during transformation.
  3. Validate quarantine isolation to S3 DLQ.
  4. Verify remaining 99 records commit successfully.
* **Expected Result:** Record #88 quarantined to S3 DLQ (`ERR-MAP-001`). Remaining 99 valid records commit to FinSight. Batch reconciliation report certifies 99 loaded, 1 quarantined, zero unaccounted discrepancy.
* **Pass/Fail Criteria:** PASS if invalid record is safely isolated and valid records commit with balanced sub-ledger audit trail.

---
