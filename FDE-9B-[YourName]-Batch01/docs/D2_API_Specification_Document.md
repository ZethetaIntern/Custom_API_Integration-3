# D2: API Specification Document & OpenAPI 3.0 Definitions
## Meridian Manufacturing Ltd. – SAP S/4HANA × Zetheta FinSight 4.2

---

| Field | Value |
|---|---|
| **Document ID** | ZA-FDE-D2-MERIDIAN-001 |
| **Version** | 1.0.0 |
| **Classification** | CONFIDENTIAL – CLIENT RESTRICTED |
| **Author** | Zetheta Algorithms – Forward Deployed Engineering (FDE-9B) |
| **OpenAPI Version** | 3.0.3 |
| **Spectral Ruleset** | `@stoplight/spectral-openapi` + `@stoplight/spectral-oas` |
| **Date** | 04 October 2026 |
| **Status** | DRAFT FOR REVIEW |

> **Companion Files:**
> - [`finsight-openapi.yaml`](./finsight-openapi.yaml) — Full OpenAPI 3.0.3 YAML (DST-001, DST-002)
> - [`D1_Integration_Architecture_v1.md`](./D1_Integration_Architecture_v1.md) — Parent architecture document

---

## Table of Contents

1. [API Architecture & Protocol Standards](#1-api-architecture--protocol-standards)
2. [Source Endpoint Catalog — SAP S/4HANA (SRC-001 → SRC-012)](#2-source-endpoint-catalog--sap-s4hana)
3. [Destination Endpoint Catalog — FinSight 4.2 (DST-001 → DST-012)](#3-destination-endpoint-catalog--finsight-42)
4. [OpenAPI 3.0.3 YAML Specification](#4-openapi-303-yaml-specification)
5. [cURL Execution Examples](#5-curl-execution-examples)
6. [Appendices](#6-appendices)

---

## 1. API Architecture & Protocol Standards

### 1.1 RESTful Design Principles

All APIs in this integration adhere to the following conventions:

| Convention | Rule | Example |
|---|---|---|
| **Base Path** | Versioned under `/api/v2/` | `/api/v2/finance/journal-entries` |
| **Resource Naming** | Plural nouns, kebab-case | `/journal-entries`, `/cost-centres` |
| **HTTP Verbs** | Strict semantic usage (see below) | `POST` create, `PUT` upsert |
| **Content-Type** | `application/json` (UTF-8) | `Content-Type: application/json; charset=utf-8` |
| **Accept** | `application/json` | `Accept: application/json` |
| **Trailing Slashes** | **Never** — 301 redirect if present | `/journal-entries` not `/journal-entries/` |
| **Response Envelope** | Consistent `data`, `meta`, `links` structure | See §1.6 |
| **Date-Time Format** | ISO 8601 with timezone (RFC 3339) | `2026-10-04T06:00:00+05:30` |
| **Amount Format** | String-encoded decimal (scale 2–4 decimal places) | `"1234567.89"` |
| **Currency Code** | ISO 4217 (3-char) | `"INR"`, `"USD"` |

#### HTTP Verb Semantics

| Verb | Semantics | Idempotent | Safe | Usage |
|---|---|---|---|---|
| `GET` | Retrieve resource(s) | Yes | Yes | Read extractions from SAP |
| `POST` | Create / bulk ingest | **No** (requires Idempotency-Key) | No | Bulk ingestion to FinSight |
| `PUT` | Upsert (full replacement) | Yes | No | Master data sync (cost centres, assets) |
| `PATCH` | Partial update | No (requires Idempotency-Key) | No | Incremental status updates |
| `DELETE` | Logical soft-delete only | Yes | No | Out-of-scope for this integration |

---

### 1.2 Authentication Mechanisms

#### 1.2.1 Source: SAP S/4HANA Gateway (mTLS + Technical Service Account)

The integration service authenticates to SAP S/4HANA via **mutual TLS (mTLS)** combined with a **SAP Technical Service Account** (`Z_FINSIGHT_ODP`). This eliminates password-based authentication and enforces certificate-level identity.

```
Authentication Flow:
  ODP Extraction Service
      │
      ├─ [Client Certificate: CN=zetheta-finsight-odp, OU=Integration]
      │      (Issued by: Meridian Internal PKI CA)
      │
      ├─ [TLS 1.3 Handshake over IPsec tunnel Port 443/3300]
      │
      └─► SAP ICM (Internet Communication Manager)
              │
              ├─ Verifies client certificate against Trust Store (STRUST)
              ├─ Maps certificate to SAP user: Z_FINSIGHT_ODP
              └─ Applies SAP Authorisation Objects:
                    S_RFC:      ACTVT=16, RFC_TYPE=FUGR, RFC_NAME=RODPS_REPL_*
                    S_TABU_DIS: ACTVT=03, DICBERCLS=FA (Finance tables, display only)
                    S_ODP_READ: DataSource=0FI_*, 0CO_*, 0IC_*, ZMM_*
                    S_ODP_NOTF: Subscribe/Acknowledge ODP delta queues
```

**SAP Authorisation Object Summary:**

| Object | Field | Value | Purpose |
|---|---|---|---|
| `S_RFC` | `ACTVT` | `16` (Execute) | RFC function module execution |
| `S_RFC` | `RFC_TYPE` | `FUGR` | Function group level |
| `S_RFC` | `RFC_NAME` | `RODPS_REPL_*` | ODP replication function group |
| `S_TABU_DIS` | `ACTVT` | `03` (Display) | Read-only table access |
| `S_TABU_DIS` | `DICBERCLS` | `FA` | Finance authorisation class |
| `S_ODP_READ` | `ODP_SRCTYPE` | `SAPI` | ODP DataSource type |
| `S_ODP_READ` | `ODP_NAME` | `0FI_*`, `0CO_*`, `ZMM_*` | Permitted DataSources |
| `S_ODP_NOTF` | `ACTVT` | `01, 02, 06` | Subscribe, modify, delete subscriber |

#### 1.2.2 Destination: FinSight 4.2 (OAuth 2.0 Client Credentials Grant)

All inbound requests to the FinSight REST API are authenticated via **OAuth 2.0 Client Credentials Grant (RFC 6749 §4.4)**.

```
Token Acquisition Flow:

  POST https://auth.finsight.zetheta.in/oauth/v2/token
  Content-Type: application/x-www-form-urlencoded

  grant_type=client_credentials
  &client_id=meridian-integration-svc
  &client_secret=<SECRET_FROM_AWS_SECRETS_MANAGER>
  &scope=finsight.gl.write finsight.ap.write finsight.ar.write
         finsight.co.write finsight.assets.write finsight.recon.read
         finsight.treasury.write finsight.procurement.write
         finsight.sales.write finsight.inventory.write

  Response:
  {
    "access_token": "<JWT>",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "finsight.gl.write finsight.ap.write ..."
  }
```

**OAuth 2.0 Scope Registry:**

| Scope | Permitted Operations | Endpoints |
|---|---|---|
| `finsight.gl.write` | Write GL journal entries | DST-001 |
| `finsight.ap.write` | Write AP items | DST-002 |
| `finsight.ar.write` | Write AR items | DST-003 |
| `finsight.co.write` | Write CO cost/profit centres and budgets | DST-004, DST-005, DST-011 |
| `finsight.inventory.write` | Write inventory and valuation | DST-006, DST-012 |
| `finsight.procurement.write` | Write purchase orders | DST-007 |
| `finsight.sales.write` | Write sales orders | DST-008 |
| `finsight.assets.write` | Write fixed asset master | DST-009 |
| `finsight.treasury.write` | Write bank statements | DST-010 |
| `finsight.recon.read` | Read reconciliation reports | EoD Recon (D1 Flow 2) |

**JWT Token Validation (FinSight API Gateway):**
- Algorithm: `RS256` (RSA-SHA256)
- JWKS Endpoint: `https://auth.finsight.zetheta.in/.well-known/jwks.json`
- Claims validated: `iss`, `sub`, `exp`, `scope`, `aud`
- Token TTL: 3,600 seconds (1 hour); refresh 5 minutes before expiry

---

### 1.3 Idempotency Protocol

**All `POST` and `PATCH` endpoints enforce the `Idempotency-Key` header.** This is critical for financial data integrity — network retries must never result in duplicate GL postings.

```
Rules:
  1. Client generates a UUID v4 Idempotency-Key for every mutation request.
  2. FinSight API stores (key → response) in Redis with TTL = 24 hours.
  3. On retry with same key: return cached response with HTTP 200 + header X-Idempotent-Replay: true
  4. On first request: process normally, cache response, return HTTP 201.
  5. Keys are scoped per client_id (from JWT sub claim).
  6. Key format: UUID v4, e.g. "f47ac10b-58cc-4372-a567-0e02b2c3d479"

Request Header:
  Idempotency-Key: f47ac10b-58cc-4372-a567-0e02b2c3d479

Response Headers (on replay):
  X-Idempotent-Replay: true
  X-Idempotent-Key: f47ac10b-58cc-4372-a567-0e02b2c3d479
  X-Idempotent-Cached-At: 2026-10-04T06:00:00Z
```

**Error Behaviour:**
- Missing `Idempotency-Key` on POST/PATCH → `HTTP 400` with `code: MISSING_IDEMPOTENCY_KEY`
- Conflicting payload with same key → `HTTP 409 Conflict` with `code: IDEMPOTENCY_CONFLICT`

---

### 1.4 Rate Limiting Headers

All FinSight API responses include rate limit headers conforming to the IETF RateLimit Headers draft:

| Header | Type | Description |
|---|---|---|
| `X-RateLimit-Limit` | integer | Maximum requests permitted per window |
| `X-RateLimit-Remaining` | integer | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp | When the current window resets (UTC epoch) |
| `X-RateLimit-Window` | integer | Window duration in seconds (default: 60) |
| `Retry-After` | integer | Seconds to wait before retrying (on HTTP 429 only) |

**Rate Limit Tiers:**

| Client Tier | Limit | Window | Burst Allowance |
|---|---|---|---|
| Integration Service (`meridian-integration-svc`) | 5,000 req | 60 seconds | 8,000 req (burst) |
| EoD Reconciliation service | 500 req | 60 seconds | 1,000 req (burst) |
| User-facing dashboard reads | 200 req | 60 seconds | 400 req (burst) |

**HTTP 429 Response:**
```json
{
  "type": "https://finsight.zetheta.in/errors/rate-limit-exceeded",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Rate limit of 5000 requests per 60 seconds exceeded.",
  "instance": "/api/v2/finance/journal-entries",
  "retryAfterSeconds": 42
}
```

---

### 1.5 Pagination Design (Cursor-Based)

All collection endpoints returning potentially large datasets use **cursor-based pagination**. Offset-based pagination is explicitly prohibited due to data consistency risks during concurrent writes.

```
Request Parameters:
  cursor  : string  (opaque cursor token from previous response; omit for first page)
  limit   : integer (max records per page; default=100, max=1000)
  sort    : string  (field to sort by; default by posting date desc)

Response Envelope:
{
  "data": [ ... ],
  "meta": {
    "totalCount":    150000,
    "returnedCount": 1000,
    "hasNextPage":   true,
    "hasPrevPage":   false
  },
  "links": {
    "self":  "/api/v2/finance/journal-entries?cursor=eyJsYXN0SWQiOjEwMDB9&limit=1000",
    "next":  "/api/v2/finance/journal-entries?cursor=eyJsYXN0SWQiOjIwMDB9&limit=1000",
    "prev":  null
  }
}

Cursor Implementation:
  - Cursor is a base64-encoded JSON object: {"lastId": 1000, "ts": "2026-10-04T05:30:00Z"}
  - Server-side: WHERE id > :lastId ORDER BY id ASC LIMIT :limit
  - Cursor is opaque to clients — never parse or construct manually
  - Cursor tokens expire after 1 hour (TTL in Redis)
```

---

### 1.6 Standard Response Envelope

```json
{
  "data":   { ... },          // Resource or array of resources
  "meta":   {
    "requestId":    "req-uuid-v4",
    "processedAt":  "2026-10-04T06:00:00.000Z",
    "apiVersion":   "2.0",
    "dataVersion":  "1.0.0",
    "totalCount":   null,
    "returnedCount": null,
    "hasNextPage":  false
  },
  "links":  {
    "self": "/api/v2/finance/journal-entries"
  }
}
```

### 1.7 Error Response Schema (RFC 7807 Problem Details)

All error responses conform to **RFC 7807 — Problem Details for HTTP APIs**:

```json
{
  "type":       "https://finsight.zetheta.in/errors/{error-code}",
  "title":      "Human-readable error summary",
  "status":     400,
  "detail":     "Machine-readable detailed description",
  "instance":   "/api/v2/finance/journal-entries",
  "requestId":  "req-f47ac10b-58cc-4372",
  "timestamp":  "2026-10-04T06:00:00.000Z",
  "errors": [
    {
      "field":   "items[0].amount",
      "code":    "INVALID_AMOUNT_FORMAT",
      "message": "Amount must be a string-encoded decimal with max 4 decimal places"
    }
  ]
}
```

---

## 2. Source Endpoint Catalog — SAP S/4HANA

> **Authentication:** All SAP source endpoints use mTLS + Technical Service Account `Z_FINSIGHT_ODP`.
> **Base URL:** `https://sap-gw.meridian.in:443`
> **OData Version:** OData V2 (SAP standard) / V4 for newer CDS views
> **Extraction Mode:** Delta (ODP) unless stated as Full

---

### SRC-001 — General Ledger Journal Entries

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-001 |
| **Path** | `/sap/opu/odata/sap/ZZ_GL_JOURNAL_CDS/JournalEntrySet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (every 30 min via `0FI_GL_14`) |
| **SAP Object** | `ACDOCA` via CDS View `I_JournalEntry` |
| **ODP Provider** | `0FI_GL_14` |

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `$filter` | string | Yes | `FiscalYear eq '2026' and PostingDate ge datetime'2026-10-04T00:00:00'` |
| `$select` | string | Yes | `CompanyCode,FiscalYear,AccountingDocument,PostingDate,GLAccount,Amount,Currency` |
| `$top` | integer | No | Max records per request (default 5000, max 10000) |
| `$skiptoken` | string | No | OData server-side paging token |
| `$orderby` | string | No | `PostingDate desc,AccountingDocument desc` |

**Response Schema (abbreviated):**

```json
{
  "d": {
    "results": [
      {
        "CompanyCode":         "1000",
        "FiscalYear":          "2026",
        "AccountingDocument":  "1400000123",
        "FiscalPeriod":        "010",
        "PostingDate":         "/Date(1759536000000)/",
        "GLAccount":           "0000400000",
        "ProfitCenter":        "PC_MH_PLANT1",
        "CostCenter":          "CC_MH_PROD_01",
        "AmountInTransCrcy":   "125000.00",
        "TransactionCurrency":  "INR",
        "AmountInCompCodeCrcy": "125000.00",
        "CompanyCodeCurrency":  "INR",
        "TaxCode":             "I8",
        "PostingKey":          "40",
        "DebitCreditCode":     "S",
        "DocumentType":        "SA",
        "LineItemText":        "Raw material purchase - Plant 1"
      }
    ],
    "__count": "150000"
  }
}
```

---

### SRC-002 — Accounts Payable Open Items

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-002 |
| **Path** | `/sap/opu/odata/sap/ZZ_AP_OPENITEMS_CDS/APOpenItemSet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min via `0FI_AP_4`) |
| **SAP Object** | `BSIK`, `BSAK`, `LFA1` |

**Key Query Parameters:** `$filter=CompanyCode eq '1000' and ClearingDate eq null`, `$select=Vendor,DocumentNumber,NetDueDate,OutstandingAmount`

**Key Response Fields:** `Vendor`, `VendorName`, `DocumentNumber`, `FiscalYear`, `NetDueDate`, `OutstandingAmount`, `Currency`, `PaymentTerms`, `PaymentBlock`, `WithholdingTaxAmount`, `TaxCode`

---

### SRC-003 — Accounts Receivable Open Items

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-003 |
| **Path** | `/sap/opu/odata/sap/ZZ_AR_OPENITEMS_CDS/AROpenItemSet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min via `0FI_AR_4`) |
| **SAP Object** | `BSID`, `BSAD`, `KNA1` |

**Key Response Fields:** `Customer`, `CustomerName`, `DocumentNumber`, `NetDueDate`, `OutstandingAmount`, `Currency`, `CreditLimit`, `OverdueAmount`, `DSO_Days`, `RiskCategory`

---

### SRC-004 — Cost Centre Master Data

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-004 |
| **Path** | `/sap/opu/odata/sap/ZZ_COSTCENTER_CDS/CostCenterSet` |
| **Method** | `GET` |
| **Extraction Mode** | Full Load (nightly, 04:30 IST post-blackout) |
| **SAP Object** | `CSKS`, `CSKT`, `SETHEADRT`, `SETLEAF` |

**Key Response Fields:** `CostCenter`, `CostCenterName`, `ControllingArea`, `CostCenterCategory`, `HierarchyNode_L1` through `HierarchyNode_L7`, `ProfitCenter`, `Plant`, `ValidFrom`, `ValidTo`, `ResponsiblePerson`

---

### SRC-005 — Profit Centre Master Data

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-005 |
| **Path** | `/sap/opu/odata/sap/ZZ_PROFITCENTER_CDS/ProfitCenterSet` |
| **Method** | `GET` |
| **Extraction Mode** | Full Load (nightly, 04:30 IST) |
| **SAP Object** | `CEPC`, `CEPCT` |

**Key Response Fields:** `ProfitCenter`, `ProfitCenterName`, `ControllingArea`, `Segment`, `HierarchyNode`, `ValidFrom`, `ValidTo`, `ProfitCenterGroup`

---

### SRC-006 — Material Ledger Actual Costing

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-006 |
| **Path** | `/sap/opu/odata/sap/ZZ_MATERIAL_VAL_CDS/MaterialLedgerSet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min via `0IC_C03`) |
| **SAP Object** | `MLHD`, `MLIT`, `CKMLCR`, `MBEW` |

**Key Response Fields:** `Material`, `Plant`, `ValuationType`, `PeriodPricePerUnit`, `StandardPrice`, `PeriodicUnitPrice`, `TotalStock`, `TotalValue`, `PriceVariance`, `ExchangeRateVariance`, `FiscalYear`, `FiscalPeriod`

---

### SRC-007 — Purchase Orders & Line Items

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-007 |
| **Path** | `/sap/opu/odata/sap/ZZ_PURCHASE_ORDERS_CDS/PurchaseOrderSet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min, changes only) |
| **SAP Object** | `EKKO`, `EKPO`, `EKET`, `EKKN` |

**Key Response Fields:** `PurchaseOrder`, `PurchaseOrderType`, `Vendor`, `Plant`, `Material`, `OrderQuantity`, `OrderUnit`, `NetOrderValue`, `Currency`, `GoodsReceiptQty`, `GoodsReceiptValue`, `InvoiceReceiptValue`, `DeliveryDate`, `AccountAssignmentCategory`, `CostCenter`, `GLAccount`

---

### SRC-008 — Sales Orders & Delivery Schedules

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-008 |
| **Path** | `/sap/opu/odata/sap/ZZ_SALES_ORDERS_CDS/SalesOrderSet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min) |
| **SAP Object** | `VBAK`, `VBAP`, `VBEP`, `VBRP` |

**Key Response Fields:** `SalesOrder`, `SalesOrderType`, `Customer`, `SalesOrg`, `Material`, `OrderQuantity`, `NetValue`, `Currency`, `ConfirmedDeliveryDate`, `RequestedDeliveryDate`, `BilledValue`, `RemainingValue`, `ProfitCenter`

---

### SRC-009 — Fixed Assets Master & Depreciation

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-009 |
| **Path** | `/sap/opu/odata/sap/ZZ_FIXED_ASSETS_CDS/AssetSet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min via `0FI_AA_11`) |
| **SAP Object** | `ANLA`, `ANLC`, `ANLZ`, `ANEK` |

**Key Response Fields:** `AssetNumber`, `SubNumber`, `AssetDescription`, `AssetClass`, `Plant`, `CostCenter`, `AcquisitionValue`, `AccumulatedDepreciation`, `NetBookValue`, `PlannedDepreciationCurrentYear`, `DepreciationKey`, `UsefulLifeYears`, `CapitalisationDate`

---

### SRC-010 — Bank Statement Line Items

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-010 |
| **Path** | `/sap/opu/odata/sap/ZZ_BANK_STMTS_CDS/BankStatementSet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min, FEBAN-driven) |
| **SAP Object** | `FEBEP`, `FEBAN`, `T012K` |

**Key Response Fields:** `BankAccount`, `BankKey`, `StatementNumber`, `StatementDate`, `LineItemAmount`, `Currency`, `ValueDate`, `TransactionCode`, `PartnerName`, `PartnerAccountNumber`, `ClearingStatus`, `OpeningBalance`, `ClosingBalance`

---

### SRC-011 — Budget vs Actual CO Totals

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-011 |
| **Path** | `/sap/opu/odata/sap/ZZ_CO_BUDGET_CDS/COBudgetSet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min via `0CO_CCA_3`) |
| **SAP Object** | `COEP`, `COSS`, `COSP`, `BPGE` |

**Key Response Fields:** `ControllingArea`, `CostCenter`, `CostElement`, `FiscalYear`, `FiscalPeriod`, `BudgetAmount`, `ActualAmount`, `CommitmentAmount`, `Variance`, `VariancePercent`, `Currency`

---

### SRC-012 — Plant Inventory & Valuation

| Field | Value |
|---|---|
| **Endpoint ID** | SRC-012 |
| **Path** | `/sap/opu/odata/sap/ZZ_INVENTORY_STOCK_CDS/InventorySet` |
| **Method** | `GET` |
| **Extraction Mode** | ODP Delta (30 min via `0IC_C03`) |
| **SAP Object** | `MARD`, `MARM`, `MSEG`, `MKPF`, `MBEW` |

**Key Response Fields:** `Material`, `Plant`, `StorageLocation`, `UnrestrictedStock`, `QualityInspectionStock`, `BlockedStock`, `InTransitStock`, `StockValue`, `MovingAveragePrice`, `StandardPrice`, `ValuationClass`, `LastGoodsMovementDate`

---

## 3. Destination Endpoint Catalog — FinSight 4.2

> **Authentication:** OAuth 2.0 Bearer JWT on all endpoints.
> **Base URL:** `https://api.finsight.zetheta.in`
> **Idempotency-Key:** Required on all POST/PATCH.
> **Batch Size:** Max 1,000 records per POST body.

---

### DST-001 — Bulk GL Journal Entry Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-001 |
| **Path** | `POST /api/v2/finance/journal-entries` |
| **Scope** | `finsight.gl.write` |
| **Max Batch** | 1,000 line items per request |
| **Idempotency** | Required |

**Request Body:** Array of journal entry document headers, each containing an array of line items with GL account, debit/credit indicator, amount in transaction and company code currency, tax split (CGST/SGST/IGST), cost object assignment, and profit centre.

**Response Codes:**

| Code | Meaning | Trigger |
|---|---|---|
| `201 Created` | Batch accepted and queued | First successful submission |
| `200 OK` | Idempotent replay | Same Idempotency-Key re-submitted |
| `400 Bad Request` | Schema validation failure | Missing required fields, invalid format |
| `401 Unauthorized` | Invalid/expired JWT | Token expired or missing |
| `403 Forbidden` | Insufficient scope | JWT missing `finsight.gl.write` |
| `409 Conflict` | Idempotency key conflict | Same key, different payload |
| `422 Unprocessable Entity` | Business rule violation | Debit ≠ Credit in journal, invalid GL account |
| `429 Too Many Requests` | Rate limit exceeded | > 5,000 req/60s |
| `500 Internal Server Error` | Platform error | Kafka unavailable, DB error |
| `503 Service Unavailable` | Circuit open | Downstream FinSight Engine unreachable |

---

### DST-002 — AP Open Items Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-002 |
| **Path** | `POST /api/v2/finance/accounts-payable/items` |
| **Scope** | `finsight.ap.write` |
| **Max Batch** | 1,000 AP items per request |
| **Idempotency** | Required |

**Request Body:** Array of AP line items including vendor, document number, fiscal year, net due date, outstanding amount, currency, payment terms, withholding tax (Section 194) details, GST input tax credit eligibility flag, and ageing bucket classification.

**Response Codes:** Same matrix as DST-001 (201, 200, 400, 401, 403, 409, 422, 429, 500, 503).

---

### DST-003 — AR Open Items Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-003 |
| **Path** | `POST /api/v2/finance/accounts-receivable/items` |
| **Scope** | `finsight.ar.write` |
| **Max Batch** | 1,000 AR items per request |
| **Idempotency** | Required |

**Request Body:** Customer, document number, net due date, outstanding amount, credit limit utilisation percentage, overdue flag, DSO days, risk category, GST TCS applicability, collection agent assignment.

---

### DST-004 — Cost Centre Upsert

| Field | Value |
|---|---|
| **Endpoint ID** | DST-004 |
| **Path** | `PUT /api/v2/co/cost-centres/{costCentreId}` |
| **Scope** | `finsight.co.write` |
| **Idempotency** | Not required (PUT is idempotent) |

**Path Parameter:** `costCentreId` — SAP Cost Centre code (alphanumeric, max 10 chars)

**Request Body:** Full cost centre master record including 7-level flattened hierarchy keys (`hierarchyL1` through `hierarchyL7`), controlling area, profit centre link, plant assignment, responsible person, validity dates.

**Response Codes:** 200 (updated), 201 (created), 400, 401, 403, 422, 500.

---

### DST-005 — Profit Centre Upsert

| Field | Value |
|---|---|
| **Endpoint ID** | DST-005 |
| **Path** | `PUT /api/v2/co/profit-centres/{profitCentreId}` |
| **Scope** | `finsight.co.write` |
| **Idempotency** | Not required (PUT is idempotent) |

**Request Body:** Profit centre master including segment classification, controlling area, hierarchy node, validity dates, associated company codes.

---

### DST-006 — Material Ledger Valuation Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-006 |
| **Path** | `POST /api/v2/inventory/valuation` |
| **Scope** | `finsight.inventory.write` |
| **Max Batch** | 1,000 valuation records |
| **Idempotency** | Required |

**Request Body:** Material, plant, fiscal period, standard price, periodic unit price, total stock, total value, price variance, exchange rate variance.

---

### DST-007 — Purchase Orders Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-007 |
| **Path** | `POST /api/v2/procurement/orders` |
| **Scope** | `finsight.procurement.write` |
| **Max Batch** | 500 PO headers (with line items nested) |
| **Idempotency** | Required |

**Request Body:** PO header + array of line items, including GR/IR status, account assignment (cost centre, GL account), delivery schedule, goods receipt quantity vs ordered quantity variance.

---

### DST-008 — Sales Orders Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-008 |
| **Path** | `POST /api/v2/sales/orders` |
| **Scope** | `finsight.sales.write` |
| **Max Batch** | 500 SO headers |
| **Idempotency** | Required |

**Request Body:** Sales order header + line items, confirmed/requested delivery date variance, billed vs remaining value, profit centre, revenue recognition status.

---

### DST-009 — Fixed Asset Master Upsert

| Field | Value |
|---|---|
| **Endpoint ID** | DST-009 |
| **Path** | `PUT /api/v2/assets/master/{assetId}` |
| **Scope** | `finsight.assets.write` |
| **Idempotency** | Not required (PUT is idempotent) |

**Path Parameter:** `assetId` — composite `{assetNumber}-{subNumber}` (e.g., `100000-0`)

**Request Body:** Full asset lifecycle record including acquisition value, accumulated depreciation, net book value, depreciation key, useful life, planned depreciation for current year, last depreciation run date.

---

### DST-010 — Bank Statement Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-010 |
| **Path** | `POST /api/v2/treasury/bank-statements` |
| **Scope** | `finsight.treasury.write` |
| **Max Batch** | 2,000 line items |
| **Idempotency** | Required |

**Request Body:** Bank statement header (account, date, opening/closing balance) + line items (transaction code, amount, value date, partner details, clearing status).

---

### DST-011 — CO Budget vs Actuals Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-011 |
| **Path** | `POST /api/v2/co/budget-actuals` |
| **Scope** | `finsight.co.write` |
| **Max Batch** | 1,000 records |
| **Idempotency** | Required |

**Request Body:** Controlling area, cost centre, cost element, fiscal year/period, budget amount, actual amount, commitment amount, variance and variance percentage.

---

### DST-012 — Multi-Plant Inventory Ingestion

| Field | Value |
|---|---|
| **Endpoint ID** | DST-012 |
| **Path** | `POST /api/v2/supplychain/inventory` |
| **Scope** | `finsight.inventory.write` |
| **Max Batch** | 2,000 records |
| **Idempotency** | Required |

**Request Body:** Material, plant, storage location, stock categories (unrestricted, quality inspection, blocked, in-transit), stock value, moving average price, valuation class, last goods movement date.

---

## 4. OpenAPI 3.0.3 YAML Specification

> **Full YAML:** See companion file [`finsight-openapi.yaml`](./finsight-openapi.yaml)
> 
> The YAML covers DST-001 (GL Journal Entries) and DST-002 (Accounts Payable) with complete
> component schemas, RFC 7807 error models, and security definitions.

Key schema components defined:

| Component | Description |
|---|---|
| `JournalEntryBatchRequest` | Root request body — array of document headers |
| `JournalEntryDocument` | Single GL document header (company code, fiscal year, doc type) |
| `JournalEntryLineItem` | GL line item (account, debit/credit, amount, tax, cost object) |
| `TaxSplit` | CGST / SGST / IGST / CESS breakdown per line item |
| `CostObject` | Cost centre, profit centre, WBS, internal order assignment |
| `MultiCurrencyAmount` | Transaction currency amount + company code currency amount + exchange rate |
| `APItemBatchRequest` | Root request body for AP items |
| `APLineItem` | Vendor, document, due date, outstanding amount, TDS section details |
| `WithholdingTax` | Section 194 TDS type, base amount, tax amount, deduction status |
| `PaginationMeta` | Standard pagination metadata |
| `ResponseLinks` | HATEOAS links (self, next, prev) |
| `ProblemDetail` | RFC 7807 error response |
| `FieldError` | Per-field validation error detail |
| `BatchIngestResponse` | Successful batch ingestion response |

---

## 5. cURL Execution Examples

### 5.1 Token Acquisition

```bash
curl --request POST \
  --url 'https://auth.finsight.zetheta.in/oauth/v2/token' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode 'client_id=meridian-integration-svc' \
  --data-urlencode 'client_secret=<SECRET>' \
  --data-urlencode 'scope=finsight.gl.write finsight.ap.write finsight.recon.read'
```

---

### 5.2 DST-001 — POST GL Journal Entries (Batch)

```bash
curl --request POST \
  --url 'https://api.finsight.zetheta.in/api/v2/finance/journal-entries' \
  --header 'Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...' \
  --header 'Content-Type: application/json; charset=utf-8' \
  --header 'Accept: application/json' \
  --header 'Idempotency-Key: f47ac10b-58cc-4372-a567-0e02b2c3d479' \
  --header 'X-Correlation-ID: corr-meridian-20261004-0600-001' \
  --header 'X-Source-System: SAP-S4HANA-PRD' \
  --header 'X-Plant-Code: MH_PLANT_01' \
  --data-raw '{
  "batchId": "batch-gl-20261004-0600-001",
  "sourceSystem": "SAP-S4HANA-PRD",
  "extractionTimestamp": "2026-10-04T06:00:00+05:30",
  "odpDeltaToken": "ODP:0FI_GL_14:MH01:2026100406000000",
  "companyCode": "1000",
  "documents": [
    {
      "accountingDocument": "1400000123",
      "companyCode": "1000",
      "fiscalYear": "2026",
      "fiscalPeriod": "010",
      "documentType": "SA",
      "postingDate": "2026-10-04",
      "entryDate": "2026-10-04",
      "documentDate": "2026-10-04",
      "documentHeaderText": "Raw material purchase - MH Plant 1",
      "referenceDocument": "PO-4500001234",
      "lineItems": [
        {
          "lineItemNumber": "001",
          "glAccount": "0000300000",
          "debitCreditCode": "S",
          "postingKey": "40",
          "amountInTransactionCurrency": {
            "amount": "125000.00",
            "currency": "INR"
          },
          "amountInCompanyCodeCurrency": {
            "amount": "125000.00",
            "currency": "INR"
          },
          "exchangeRate": "1.000000",
          "taxCode": "I8",
          "taxSplit": {
            "cgstAmount": "5625.00",
            "sgstAmount": "5625.00",
            "igstAmount": "0.00",
            "cessAmount": "0.00",
            "taxCurrency": "INR"
          },
          "costObject": {
            "costCenter": "CC_MH_PROD_01",
            "profitCenter": "PC_MH_PLANT1",
            "wbsElement": null,
            "internalOrder": null
          },
          "lineItemText": "Steel coils 500MT - Supplier INV-2026-9823",
          "assignment": "PO-4500001234-001"
        },
        {
          "lineItemNumber": "002",
          "glAccount": "0000200000",
          "debitCreditCode": "H",
          "postingKey": "50",
          "amountInTransactionCurrency": {
            "amount": "125000.00",
            "currency": "INR"
          },
          "amountInCompanyCodeCurrency": {
            "amount": "125000.00",
            "currency": "INR"
          },
          "exchangeRate": "1.000000",
          "taxCode": null,
          "taxSplit": null,
          "costObject": null,
          "lineItemText": "Vendor payable - TATA STEEL LTD",
          "assignment": "PO-4500001234-001"
        }
      ]
    }
  ]
}'
```

**Expected Response (201 Created):**

```json
{
  "data": {
    "batchId": "batch-gl-20261004-0600-001",
    "status": "ACCEPTED",
    "acceptedDocuments": 1,
    "acceptedLineItems": 2,
    "rejectedDocuments": 0,
    "pipelineEventId": "evt-kafka-sap.delta.transformed-p12-o44821",
    "estimatedProcessingTime": "PT30S"
  },
  "meta": {
    "requestId": "req-f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "processedAt": "2026-10-04T00:30:01.123Z",
    "apiVersion": "2.0"
  },
  "links": {
    "self": "/api/v2/finance/journal-entries",
    "status": "/api/v2/finance/journal-entries/batch/batch-gl-20261004-0600-001"
  }
}
```

---

### 5.3 DST-001 — HTTP 422 Business Rule Violation (Unbalanced Journal)

```json
{
  "type": "https://finsight.zetheta.in/errors/journal-entry-unbalanced",
  "title": "Unprocessable Journal Entry",
  "status": 422,
  "detail": "Journal entry 1400000123 is unbalanced: total debits INR 125000.00 ≠ total credits INR 120000.00. Difference: INR 5000.00.",
  "instance": "/api/v2/finance/journal-entries",
  "requestId": "req-f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "timestamp": "2026-10-04T00:30:01.456Z",
  "errors": [
    {
      "field": "documents[0]",
      "code": "JOURNAL_UNBALANCED",
      "message": "Debit total (125000.00 INR) must equal credit total (120000.00 INR)"
    }
  ]
}
```

---

### 5.4 DST-002 — POST AP Open Items (Batch)

```bash
curl --request POST \
  --url 'https://api.finsight.zetheta.in/api/v2/finance/accounts-payable/items' \
  --header 'Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...' \
  --header 'Content-Type: application/json; charset=utf-8' \
  --header 'Accept: application/json' \
  --header 'Idempotency-Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890' \
  --header 'X-Correlation-ID: corr-meridian-20261004-0600-002' \
  --header 'X-Source-System: SAP-S4HANA-PRD' \
  --data-raw '{
  "batchId": "batch-ap-20261004-0600-001",
  "sourceSystem": "SAP-S4HANA-PRD",
  "extractionTimestamp": "2026-10-04T06:00:00+05:30",
  "companyCode": "1000",
  "items": [
    {
      "vendor": "VENDOR_0010012345",
      "vendorName": "TATA STEEL LIMITED",
      "companyCode": "1000",
      "documentNumber": "1900000456",
      "fiscalYear": "2026",
      "documentType": "KR",
      "postingDate": "2026-09-25",
      "documentDate": "2026-09-20",
      "netDueDate": "2026-10-25",
      "outstandingAmount": {
        "amount": "3450000.00",
        "currency": "INR"
      },
      "paymentTerms": "NT30",
      "paymentBlock": null,
      "paymentMethod": "T",
      "bankKey": "HDFC0000123",
      "bankAccount": "50100123456789",
      "ageingBucket": "CURRENT",
      "daysOverdue": 0,
      "withholdingTax": {
        "section": "194C",
        "taxType": "C1",
        "baseAmount": "3450000.00",
        "taxRate": "2.00",
        "taxAmount": "69000.00",
        "surchargeAmount": "0.00",
        "cessAmount": "2760.00",
        "totalTdsAmount": "71760.00",
        "deductionStatus": "DEDUCTED",
        "tdsDeductedDate": "2026-09-25",
        "currency": "INR"
      },
      "gstInputTaxCreditEligible": true,
      "gstTaxCode": "I8",
      "invoiceReference": "TATA-INV-2026-98234",
      "purchaseOrderReference": "4500001234"
    }
  ]
}'
```

---

### 5.5 DST-004 — PUT Cost Centre (Upsert with 7-Level Hierarchy)

```bash
curl --request PUT \
  --url 'https://api.finsight.zetheta.in/api/v2/co/cost-centres/CC_MH_PROD_01' \
  --header 'Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...' \
  --header 'Content-Type: application/json; charset=utf-8' \
  --data-raw '{
  "costCenterId": "CC_MH_PROD_01",
  "costCenterName": "Maharashtra Plant 1 - Production",
  "controllingArea": "MFGL",
  "costCenterCategory": "P",
  "plant": "MH01",
  "profitCenter": "PC_MH_PLANT1",
  "hierarchy": {
    "hierarchyL1": "MERIDIAN_GROUP",
    "hierarchyL2": "MANUFACTURING_DIV",
    "hierarchyL3": "MAHARASHTRA_REGION",
    "hierarchyL4": "PLANT_MH01",
    "hierarchyL5": "PRODUCTION_DEPT",
    "hierarchyL6": "ASSEMBLY_LINE_A",
    "hierarchyL7": "CC_MH_PROD_01"
  },
  "responsiblePerson": "Rajesh Kumar",
  "validFrom": "2026-04-01",
  "validTo": "9999-12-31",
  "currency": "INR",
  "businessArea": "BA_MH"
}'
```

---

## 6. Appendices

### Appendix A: Endpoint Cross-Reference Matrix

| Source Endpoint | Maps To | FinSight Target | Kafka Topic | ODP Provider |
|---|---|---|---|---|
| SRC-001 (GL) | → | DST-001 | `sap.delta.transformed.gl` | `0FI_GL_14` |
| SRC-002 (AP) | → | DST-002 | `sap.delta.transformed.ap` | `0FI_AP_4` |
| SRC-003 (AR) | → | DST-003 | `sap.delta.transformed.ar` | `0FI_AR_4` |
| SRC-004 (Cost Centre) | → | DST-004 | `sap.delta.transformed.co-master` | Full Load |
| SRC-005 (Profit Centre) | → | DST-005 | `sap.delta.transformed.co-master` | Full Load |
| SRC-006 (Material Ledger) | → | DST-006 | `sap.delta.transformed.inventory` | `0IC_C03` |
| SRC-007 (PO) | → | DST-007 | `sap.delta.transformed.procurement` | Custom |
| SRC-008 (SO) | → | DST-008 | `sap.delta.transformed.sales` | Custom |
| SRC-009 (Assets) | → | DST-009 | `sap.delta.transformed.assets` | `0FI_AA_11` |
| SRC-010 (Bank) | → | DST-010 | `sap.delta.transformed.treasury` | Custom |
| SRC-011 (Budget) | → | DST-011 | `sap.delta.transformed.co-budget` | `0CO_CCA_3` |
| SRC-012 (Inventory) | → | DST-012 | `sap.delta.transformed.inventory` | `0IC_C03` |

### Appendix B: HTTP Response Code Reference

| Code | Name | When Used |
|---|---|---|
| `200 OK` | OK | GET success; Idempotent POST replay |
| `201 Created` | Created | First-time POST success |
| `400 Bad Request` | Bad Request | Schema validation failure, missing required fields |
| `401 Unauthorized` | Unauthorized | JWT missing, expired, or malformed |
| `403 Forbidden` | Forbidden | JWT valid but scope insufficient |
| `409 Conflict` | Conflict | Idempotency-Key submitted with different payload |
| `422 Unprocessable Entity` | Unprocessable | Business rule violation (unbalanced journal, invalid GL) |
| `429 Too Many Requests` | Rate Limited | Client exceeded rate limit tier |
| `500 Internal Server Error` | Server Error | Unhandled exception, Kafka unavailable |
| `503 Service Unavailable` | Unavailable | Circuit breaker OPEN, downstream timeout |

### Appendix C: Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 22 Sep 2026 | Zetheta FDE-9B | Initial endpoint catalog draft |
| 0.5 | 30 Sep 2026 | Zetheta FDE-9B | Added OpenAPI YAML, cURL examples |
| 1.0 | 04 Oct 2026 | Zetheta FDE-9B | Production-ready draft |

---

*Document Classification: CONFIDENTIAL – CLIENT RESTRICTED*
*© 2026 Zetheta Algorithms Pvt. Ltd. All rights reserved.*
*Reference: ZA-FDE-D2-MERIDIAN-001 v1.0.0 | 04 October 2026*
