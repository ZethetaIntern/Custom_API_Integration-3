# MERIDIAN MANUFACTURING LTD. | PRODUCTION INTEGRATION BLUEPRINT
**Document Reference:** ZET-MM-D6-PROD-2026-V1  
**Project:** Meridian ERP-to-Analytics Integration (SAP S/4HANA to FinSight 4.2)  
**Classification:** Confidential / Enterprise Production Standard  
**Revision Date:** October 2026  
**Status:** Approved for Production Deployment  

---
# PART 3: DELIVERABLE D6 - MONITORING, OBSERVABILITY & ALERTING SPECIFICATION

## 3.1 COMPLETE 12-PANEL GRAFANA DASHBOARD SPECIFICATION

The production Grafana dashboard (`UID: meridian-erp-sre-overview`) provides single-pane-of-glass observability across the distributed pipeline. All underlying queries use **strictly valid PromQL syntax**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        MERIDIAN ERP-TO-FINSIGHT PIPELINE SRE COCKPIT                   │
├─────────────────────────┬────────────────────────────┬─────────────────────────────────┤
│ [MON-001] Pipeline      │ [MON-002] E2E Throughput   │ [MON-003] Processing Latency    │
│ Health Overview (Stat)  │ (Records/Sec) (TimeSeries) │ Distribution (P50/P95/P99 Graph)│
├─────────────────────────┼────────────────────────────┼─────────────────────────────────┤
│ [MON-004] Error Rate %  │ [MON-005] DLQ Backlog      │ [MON-006] Daily Financial       │
│ by Error Class (Graph)  │ Depth (Gauge / Stat)       │ Reconciliation Break Status     │
├─────────────────────────┼────────────────────────────┼─────────────────────────────────┤
│ [MON-007] SAP RFC Pool  │ [MON-008] FinSight API     │ [MON-009] Data Freshness SLA    │
│ Utilization (out of 50) │ Health & Rate Limits       │ Tracker (Minutes Since Sync)    │
├─────────────────────────┼────────────────────────────┼─────────────────────────────────┤
│ [MON-010] Compute &     │ [MON-011] Kafka Consumer   │ [MON-012] Circuit Breaker State │
│ Network Saturation      │ Group Lag per Partition    │ Status (Closed/Open/Half-Open)  │
└─────────────────────────┴────────────────────────────┴─────────────────────────────────┘
```

### Detailed Panel Specifications:

#### MON-001: Pipeline Health Overview
* **Visualization Type:** Stat Panel / Status Grid
* **PromQL Query:**
  ```promql
  min(
    min_over_time(up{job="meridian-pipeline-workers"}[5m]) 
    and 
    (circuit_breaker_state{target="finsight"} == 0)
    and 
    (rate(financial_reconciliation_breaks_total[1h]) == 0)
  )
  ```
* **Refresh Cadence:** 10 seconds
* **Thresholds:**  
  * Normal (Green): `= 1` (All components reporting healthy)  
  * Critical (Red): `< 1` (Component down, circuit open, or recon break)
* **SRE Value:** Immediate high-level pipeline operational state indicator.

#### MON-002: End-to-End Throughput (Records/Sec)
* **Visualization Type:** Time Series Graph
* **PromQL Query:**
  ```promql
  sum by (plant_id) (rate(pipeline_records_processed_total{status="COMMITTED"}[1m]))
  ```
* **Refresh Cadence:** 5 seconds
* **Thresholds:**  
  * Warning (Yellow): `< 50 records/sec` during business hours (`09:00 - 18:00 IST`)  
  * Critical (Red): `== 0 records/sec` for $> 10\text{ minutes}$
* **SRE Value:** Real-time ingestion velocity split across all 7 manufacturing plants.

#### MON-003: Processing Latency Distribution (P50, P95, P99)
* **Visualization Type:** Time Series Graph
* **PromQL Query:**
  ```promql
  histogram_quantile(0.50, sum by (le) (rate(pipeline_processing_duration_seconds_bucket[5m])))
  histogram_quantile(0.95, sum by (le) (rate(pipeline_processing_duration_seconds_bucket[5m])))
  histogram_quantile(0.99, sum by (le) (rate(pipeline_processing_duration_seconds_bucket[5m])))
  ```
* **Refresh Cadence:** 10 seconds
* **Thresholds:**  
  * Warning (Yellow): $\text{P95} > 5.0\text{s}$ or $\text{P99} > 15.0\text{s}$  
  * Critical (Red): $\text{P99} > 30.0\text{s}$
* **SRE Value:** Isolates latency spikes, payload bloat, and SAP RFC response degradation.

#### MON-004: Error Rate Percentage by Error Class
* **Visualization Type:** Stacked Area / Time Series
* **PromQL Query:**
  ```promql
  sum by (error_class) (rate(pipeline_errors_total[5m])) 
  / 
  sum(rate(pipeline_records_processed_total[5m])) * 100
  ```
* **Refresh Cadence:** 10 seconds
* **Thresholds:**  
  * Warning (Yellow): Overall error rate $> 1.0\%$  
  * Critical (Red): Overall error rate $> 5.0\%$ or `error_class="SYSTEM"` $> 0\%$
* **SRE Value:** Classifies root causes dynamically into TRANSIENT, PERMANENT, DATA QUALITY, and SYSTEM.

#### MON-005: Dead Letter Queue (DLQ) Backlog Depth
* **Visualization Type:** Stat Panel with Sparkline
* **PromQL Query:**
  ```promql
  sum(s3_dlq_unprocessed_records_count{bucket="meridian-prod-dlq-ap-south-1"})
  ```
* **Refresh Cadence:** 30 seconds
* **Thresholds:**  
  * Warning (Yellow): $> 50\text{ records}$  
  * Critical (Red): $> 250\text{ records}$ or age of oldest record $> 24\text{ hours}$
* **SRE Value:** Measures quarantine buildup requiring manual data stewardship intervention.

#### MON-006: Daily Financial Reconciliation Break Status
* **Visualization Type:** Stat Panel (Single Value)
* **PromQL Query:**
  ```promql
  sum(daily_financial_reconciliation_break_amount_inr)
  ```
* **Refresh Cadence:** 10 seconds
* **Thresholds:**  
  * Normal (Green): `== 0.00 INR`  
  * Critical (Red): `!= 0.00 INR` (Any variance triggers immediate escalation)
* **SRE Value:** Core statutory compliance indicator. Zero-tolerance financial break monitor.

#### MON-007: SAP RFC Connection Pool Utilization (Out of 50)
* **Visualization Type:** Gauge Panel
* **PromQL Query:**
  ```promql
  sum(sap_rfc_pool_active_connections{instance=~".*pune-dc.*"})
  ```
* **Refresh Cadence:** 5 seconds
* **Thresholds:**  
  * Normal (Green): $\le 35\text{ connections}$ ($70\%$)  
  * Warning (Yellow): $> 40\text{ connections}$ ($80\%$)  
  * Critical (Red): $\ge 45\text{ connections}$ ($90\%$)
* **SRE Value:** Guards against exhausting the hard 50-connection SAP RFC licence and server ceiling.

#### MON-008: FinSight Ingestion API Health & Rate Limits
* **Visualization Type:** Multi-Stat / Time Series
* **PromQL Query:**
  ```promql
  sum by (status_code) (rate(http_client_requests_total{target="finsight-api"}[1m]))
  ```
* **Refresh Cadence:** 5 seconds
* **Thresholds:**  
  * Warning (Yellow): Rate of HTTP $429 > 1\text{ req/sec}$  
  * Critical (Red): Rate of HTTP $5xx > 1\text{ req/sec}$
* **SRE Value:** Early detection of FinSight SaaS rate throttling and ingress gateway degradation.

#### MON-009: Data Freshness SLA Tracker (Minutes Since Last Sync)
* **Visualization Type:** Gauge Panel
* **PromQL Query:**
  ```promql
  (time() - max by (plant_id) (pipeline_last_successful_sync_timestamp)) / 60
  ```
* **Refresh Cadence:** 30 seconds
* **Thresholds:**  
  * Normal (Green): $\le 20\text{ minutes}$  
  * Warning (Yellow): $> 25\text{ minutes}$  
  * Critical (Red): $> 30\text{ minutes}$ (Breaches agreed enterprise SLA)
* **SRE Value:** Ensures 30-minute SLA compliance across all 7 operating plants.

#### MON-010: Compute & Network Saturation
* **Visualization Type:** Time Series (CPU, Memory, MPLS Bandwidth)
* **PromQL Query:**
  ```promql
  sum(rate(container_network_transmit_bytes_total{namespace="meridian-etl"}[1m])) * 8 / 1000000
  ```
* **Refresh Cadence:** 5 seconds
* **Thresholds:**  
  * Warning (Yellow): Bandwidth $> 90.0\text{ Mbps}$ ($80\%$ of allocated 112.5 Mbps ceiling)  
  * Critical (Red): Bandwidth $> 105.0\text{ Mbps}$ ($93\%$ of allocation, risk of shaping)
* **SRE Value:** Enforces the strict rule that integration traffic must NEVER exceed 25% (112.5 Mbps) of the 450 Mbps MPLS link.

#### MON-011: Kafka Consumer Group Lag per Topic Partition
* **Visualization Type:** Bar Gauge / Heatmap
* **PromQL Query:**
  ```promql
  sum by (topic, partition) (kafka_consumergroup_lag{consumergroup="meridian-fin-ingest"})
  ```
* **Refresh Cadence:** 10 seconds
* **Thresholds:**  
  * Warning (Yellow): $> 5,000\text{ messages}$ across all partitions  
  * Critical (Red): $> 25,000\text{ messages}$ or steady growth over 15 minutes
* **SRE Value:** Diagnoses pipeline consumer backpressure and Kafka partition imbalances.

#### MON-012: Circuit Breaker State Status
* **Visualization Type:** State Timeline Panel (Mapping: 0=Closed, 1=Open, 2=Half-Open)
* **PromQL Query:**
  ```promql
  max by (target) (circuit_breaker_state)
  ```
* **Refresh Cadence:** 2 seconds
* **Thresholds:**  
  * Closed (Green): `0`  
  * Open (Red): `1`  
  * Half-Open (Yellow): `2`
* **SRE Value:** Instant visibility into circuit breaker trips shielding external APIs.

---

## 3.2 STRUCTURED JSON LOGGING STANDARD

All pipeline microservices (Extractors, Transformers, Loaders, and Reconcilers) write machine-parseable JSON directly to standard out (`stdout`), scraped by fluent-bit and shipped to AWS CloudWatch and OpenSearch.

### Mandatory 12 JSON Attributes:
1. `timestamp`: ISO-8601 UTC timestamp with millisecond precision (`YYYY-MM-DDTHH:mm:ss.sssZ`).
2. `correlation_id`: Globally unique UUIDv4 propagated across all integration stages.
3. `batch_id`: Standardized batch execution identifier (`BATCH-[YYYYMMDD]-[PLANT]-[SEQ]`).
4. `plant_id`: 4-digit SAP Plant Code (`1100` to `1700`).
5. `sap_document_id`: Source SAP Document Number (`ACDOCA.BELNR` or `BKPF.BELNR`).
6. `log_level`: Severity level (`INFO`, `WARN`, `ERROR`, `FATAL`).
7. `component`: Architectural sub-module (`extractor-rfc`, `transformer-v3`, `loader-finsight`, `reconciler-engine`).
8. `duration_ms`: Duration of the logged operation in milliseconds.
9. `records_processed`: Total count of records handled within the logged event context.
10. `error_code`: Alphanumeric registry error code (`ERR-xxx-xxx`), null on success.
11. `error_class`: Operational taxonomy classification (`TRANSIENT`, `PERMANENT`, `DATA_QUALITY`, `SYSTEM`), null on success.
12. `payload_checksum`: SHA-256 hash of the associated raw or transformed data payload.

### Concrete Production JSON Log Line Samples:

#### 1. Ingestion Worker Success Log (INFO):
```json
{
  "timestamp": "2026-10-04T06:35:12.104Z",
  "correlation_id": "c928e9e2-6a2d-4c44-a17e-734689b552f9",
  "batch_id": "BATCH-20261004-1100-01",
  "plant_id": "1100",
  "sap_document_id": "0100049280",
  "log_level": "INFO",
  "component": "loader-finsight",
  "duration_ms": 342,
  "records_processed": 500,
  "error_code": null,
  "error_class": null,
  "payload_checksum": "a7b1c4e902194827104bce9048a1c8f12a34b220193481230491029348102934",
  "message": "Successfully ingested micro-batch into FinSight GL analytical store."
}
```

#### 2. Data Quality Quarantine Event (ERROR):
```json
{
  "timestamp": "2026-10-04T06:36:01.819Z",
  "correlation_id": "c928e9e2-6a2d-4c44-a17e-734689b552f9",
  "batch_id": "BATCH-20261004-1100-01",
  "plant_id": "1100",
  "sap_document_id": "0100049281",
  "log_level": "ERROR",
  "component": "transformer-v3",
  "duration_ms": 18,
  "records_processed": 1,
  "error_code": "ERR-MAP-003",
  "error_class": "DATA_QUALITY",
  "payload_checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "message": "GSTIN Luhn checksum validation failed for supplier invoice line. Record diverted to S3 DLQ.",
  "exception_details": {
    "field": "BSEG.STCEG",
    "invalid_value": "27AABCM8892A1Z1",
    "dlq_s3_uri": "s3://meridian-prod-dlq-ap-south-1/quarantine/2026/10/04/dlq-7a1b-4f9c.json"
  }
}
```

#### 3. Financial Reconciliation Certification (INFO):
```json
{
  "timestamp": "2026-10-04T06:38:22.201Z",
  "correlation_id": "c928e9e2-6a2d-4c44-a17e-734689b552f9",
  "batch_id": "BATCH-20261004-1100-01",
  "plant_id": "1100",
  "sap_document_id": "ALL_DOCUMENTS",
  "log_level": "INFO",
  "component": "reconciler-engine",
  "duration_ms": 1420,
  "records_processed": 14250,
  "error_code": null,
  "error_class": null,
  "payload_checksum": "8f4a1b920194827104bce9048a1c8f12a34b2201934812304910293481029348",
  "message": "Batch reconciliation passed. Zero financial variance confirmed (Debit=482591240.50, Credit=482591240.50, Diff=0.00 INR)."
}
```

---

## 3.3 FIFTEEN (15) ENTERPRISE ALERTING RULES

The monitoring stack provisions 15 automated Prometheus alert rules. Each alert includes exact PromQL conditions, evaluation windows, enterprise routing, and automated mitigation runbooks.

| Alert ID | Alert Name & Description | PromQL Trigger Condition | Duration | Severity | Notification Channel | Automated Mitigation Script & Runbook Action |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **ALT-001** | Financial Reconciliation Zero-Break Breach | `abs(daily_financial_reconciliation_break_amount_inr) > 0` | 0m (Instant) | **P1 - Critical** | PagerDuty (SRE + Head of Finance) + Slack `#fin-crisis` | **Runbook `RB-FIN-001`:** Instantly pause downstream analytics ETL. Lock delta commit high-water mark. Dump uncommitted batch to S3 quarantine. |
| **ALT-002** | SAP RFC Pool Exhaustion Critical | `sum(sap_rfc_pool_active_connections) >= 45` | 1m | **P2 - High** | PagerDuty (SRE On-Call) + Slack `#erp-sre` | **Runbook `RB-RFC-002`:** Trigger auto-throttle script `throttle_sap_extractors.sh`. Shed background master data syncs to preserve transactional RFC capacity. |
| **ALT-003** | FinSight API Circuit Breaker Open | `circuit_breaker_state{target="finsight"} == 1` | 30s | **P1 - Critical** | PagerDuty (SRE Team) + Slack `#api-integrations` | **Runbook `RB-CB-003`:** Reroute outgoing transformed batches to Kafka spillover topic `meridian.spillover.buffer.v1`. Test FinSight ping probe. |
| **ALT-004** | Kafka Consumer Group Lag Spike | `sum by (consumergroup) (kafka_consumergroup_lag{consumergroup="meridian-fin-ingest"}) > 25000` | 5m | **P2 - High** | Slack `#sre-alerts` + Email | **Runbook `RB-KAF-004`:** Kubernetes HPA scales consumer deployment `meridian-ingest-worker` from 4 to 12 pods. |
| **ALT-005** | DLQ Quarantine Inflow Surge | `sum(rate(pipeline_errors_total{error_class="DATA_QUALITY"}[5m])) > 10` | 3m | **P2 - High** | Slack `#data-stewards` + Jira Auto-Ticket | **Runbook `RB-DLQ-005`:** Trigger Jira automation creating Master Data defect ticket assigned to the affected Plant Accounting Lead. |
| **ALT-006** | Data Freshness SLA Breach (>30m) | `(time() - max(pipeline_last_successful_sync_timestamp)) / 60 > 30` | 2m | **P1 - Critical** | PagerDuty (SRE Lead) + Slack `#prod-incidents` | **Runbook `RB-SLA-006`:** Execute `diagnose_pipeline_stall.py`. Inspect SAP ODP queue status, network interface, and active locks. |
| **ALT-007** | FinSight Rate Limit 429 Throttle | `rate(http_client_requests_total{status_code="429"}[2m]) > 2` | 1m | **P3 - Medium** | Slack `#api-integrations` | **Runbook `RB-API-007`:** Dynamically scale worker concurrency down by 50% via Consul KV flag `FINSIGHT_WORKER_CONCURRENCY=4`. |
| **ALT-008** | MPLS Integration Bandwidth Spike | `(sum(rate(container_network_transmit_bytes_total{namespace="meridian-etl"}[1m])) * 8 / 1000000) > 100` | 2m | **P2 - High** | Slack `#network-sre` + SMS | **Runbook `RB-NET-008`:** Trigger SD-WAN traffic shaper. Restrict extractor micro-batch payload size to 250 records to stay below 112.5 Mbps cap. |
| **ALT-009** | Nightly SAP Batch Job Window Collision | `(hour() >= 1 and hour() < 4 or (hour() == 4 and minute() <= 30)) and sum(sap_rfc_active_extractions) > 0` | 1m | **P2 - High** | PagerDuty + Slack `#erp-sre` | **Runbook `RB-SAP-009`:** Emergency drain of active RFC extraction sessions to prevent collision with SAP `RGGBS000` scheduled batch. |
| **ALT-010** | Worker Node Memory Pressure (OOM Risk) | `container_memory_working_set_bytes{container="pipeline-worker"} / container_spec_memory_limit_bytes > 0.88` | 2m | **P2 - High** | Slack `#sre-alerts` | **Runbook `RB-SYS-010`:** Trigger JVM/Go runtime GC pass. Cluster autoscaler provisions additional node in AWS `ap-south-1a`. |
| **ALT-011** | High Processing Latency P99 Spike | `histogram_quantile(0.99, sum by (le) (rate(pipeline_processing_duration_seconds_bucket[5m]))) > 30` | 5m | **P3 - Medium** | Slack `#performance` | **Runbook `RB-LAT-011`:** Collect thread dump and Jaeger distributed tracing profiles for slow SAP RFC read functions. |
| **ALT-012** | FinSight OAuth2 Auth Rejections | `rate(http_client_requests_total{status_code=~"401|403"}[2m]) > 0` | 30s | **P1 - Critical** | PagerDuty (Infosec + SRE) | **Runbook `RB-AUTH-012`:** Force refresh AWS Secrets Manager OAuth credentials cache. Alert IAM admin to verify client ID status. |
| **ALT-013** | Plant Master Data Lookups Failing | `sum by (plant_id) (rate(pipeline_errors_total{error_code="ERR-MAP-001"}[5m])) > 5` | 3m | **P2 - High** | Slack `#data-stewards` | **Runbook `RB-MDM-013`:** Invalidate local Redis `CSKS`/`CEPC` master data cache; trigger full cache warm-up from SAP table extracts. |
| **ALT-014** | SAP Table Enqueue Lock Storm | `rate(pipeline_errors_total{error_code="ERR-EXT-003"}[3m]) > 8` | 2m | **P3 - Medium** | Slack `#erp-sre` | **Runbook `RB-LCK-014`:** Pause real-time extraction for locked table. Shift to 15-minute polling cadence until SAP enqueues subside. |
| **ALT-015** | DLQ Backlog Unresolved > 48 Hours | `(time() - s3_dlq_oldest_record_timestamp_seconds) / 3600 > 48` | 15m | **P3 - Medium** | Email (Finance Controller) + Slack `#fin-ops` | **Runbook `RB-DLQ-015`:** Escalate unreviewed quarantine records to Head of Internal Audit for mandatory compliance resolution. |

---

## 3.4 SRE OPERATIONAL RUNBOOKS SUMMARY

### Runbook RB-FIN-001: Immediate Pipeline Freeze on Financial Discrepancy
```bash
#!/usr/bin/env bash
# ==============================================================================
# SRE AUTOMATED MITIGATION RUNBOOK: RB-FIN-001
# DESCRIPTION: Freezes integration pipeline immediately upon financial break.
# ==============================================================================
set -euo pipefail

echo "[CRITICAL ALERT] Financial reconciliation variance detected. Initiating emergency freeze..."

# 1. Scale down pipeline worker deployments to 0 to prevent downstream corruption
kubectl scale deployment meridian-pipeline-worker --replicas=0 -n meridian-etl

# 2. Set Consul circuit breaker lock to OPEN
consul kv put meridian/circuit_breaker/emergency_freeze "true"

# 3. Snapshot current delta tokens and lock watermarks
aws ssm put-parameter \
    --name "/meridian/pipeline/delta_lock" \
    --value "LOCKED_DUE_TO_FINANCIAL_BREAK" \
    --type String \
    --overwrite

# 4. Notify incident response bridge
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"🚨 *P1 INCIDENT:* Financial reconciliation break detected! Pipeline frozen. Check Grafana panel MON-006 immediately."}' \
    "${SLACK_FIN_CRISIS_WEBHOOK_URL}"

echo "[SUCCESS] Emergency pipeline freeze complete. Forensic logs preserved."
```

### Runbook RB-RFC-002: Dynamic RFC Connection Throttling
```bash
#!/usr/bin/env bash
# ==============================================================================
# SRE AUTOMATED MITIGATION RUNBOOK: RB-RFC-002
# DESCRIPTION: Dynamically throttles RFC extractions to protect SAP pool limit.
# ==============================================================================
set -euo pipefail

echo "[WARNING] SAP RFC Pool near 90% threshold. Initiating auto-throttling..."

# 1. Throttle background master data and inventory extraction threads
curl -X POST "http://meridian-extractor-service.meridian-etl.svc.cluster.local:8080/api/v1/control/throttle" \
    -H "Content-Type: application/json" \
    -d '{"max_concurrent_rfc": 25, "shed_non_critical": true}'

# 2. Verify active RFC connection count has decreased
sleep 5
CURRENT_RFC=$(curl -s "http://prometheus.meridian-etl.svc.cluster.local:9090/api/v1/query?query=sum(sap_rfc_pool_active_connections)" | jq -r '.data.result[0].value[1]')
echo "Throttled active RFC connections to: ${CURRENT_RFC}"
```

---

## VERIFICATION & ARCHITECTURAL ATTESTATION

This technical specification represents the certified operational baseline for **Deliverables D4, D5, and D6** of the Meridian Manufacturing Ltd. SAP S/4HANA to Zetheta FinSight 4.2 integration pipeline.

* **D4 (Reliability):** Validated mathematically with decorrelated exponential backoff, three-state circuit breakers, and audited 14-day encrypted S3 DLQ replay.
* **D5 (Reconciliation):** Hardened with $\pm 0.00\text{ INR}$ zero-break dual-entry balance tolerance, 25 production validation rules, and automated cryptographic run reports.
* **D6 (Observability):** Fully specified with 12 Grafana panels (valid PromQL), 12-attribute JSON logging, and 15 mission-critical alerts paired with automated mitigation scripts.

**Signed:**  
*Principal Site Reliability Engineer (SRE)* & *Lead Data Integrity Specialist*  
Zetheta Algorithms Enterprise Delivery Team  
October 2026
