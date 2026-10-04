# D3: Data Transformation and Mapping Specification
## Meridian Manufacturing Ltd. — SAP S/4HANA → Zetheta FinSight 4.2

---

| Field | Value |
|---|---|
| **Document ID** | ZA-FDE-D3-MERIDIAN-001 |
| **Version** | 1.0.0 |
| **Classification** | CONFIDENTIAL – CLIENT RESTRICTED |
| **Author** | Zetheta Algorithms – Forward Deployed Engineering (FDE-9B) |
| **Parent Documents** | D1 (ZA-FDE-D1-MERIDIAN-001), D2 (ZA-FDE-D2-MERIDIAN-001) |
| **Total Mappings** | **54 field-level mappings across 10 domains** |
| **Date** | 04 October 2026 |
| **Status** | DRAFT FOR REVIEW |

---

## Table of Contents

1. [Mapping Standards & Conventions](#1-mapping-standards--conventions)
2. [Domain 1 — General Ledger Accounting (MAP-GL-001 → MAP-GL-012)](#2-domain-1--general-ledger-accounting)
3. [Domain 2 — Accounts Payable (MAP-AP-001 → MAP-AP-008)](#3-domain-2--accounts-payable)
4. [Domain 3 — Accounts Receivable (MAP-AR-001 → MAP-AR-008)](#4-domain-3--accounts-receivable)
5. [Domain 4 — Cost Centre Accounting (MAP-CO-001 → MAP-CO-006)](#5-domain-4--cost-centre-accounting)
6. [Domain 5 — Profit Centre Accounting (MAP-PC-001 → MAP-PC-004)](#6-domain-5--profit-centre-accounting)
7. [Domain 6 — Material Ledger & Valuation (MAP-ML-001 → MAP-ML-004)](#7-domain-6--material-ledger--valuation)
8. [Domain 7 — Purchase Orders & Procurement (MAP-PO-001 → MAP-PO-004)](#8-domain-7--purchase-orders--procurement)
9. [Domain 8 — Sales Orders (MAP-SO-001 → MAP-SO-003)](#9-domain-8--sales-orders)
10. [Domain 9 — Fixed Assets (MAP-FA-001 → MAP-FA-002)](#10-domain-9--fixed-assets)
11. [Domain 10 — Bank Statements & Cash (MAP-BK-001 → MAP-BK-003)](#11-domain-10--bank-statements--cash)
12. [Algorithm A — Recursive Hierarchy Flattening (SETNODE/SETLEAF)](#12-algorithm-a--recursive-hierarchy-flattening)
13. [Algorithm B — TCURR Triangulation & Point-in-Time Rate Lookup](#13-algorithm-b--tcurr-triangulation--point-in-time-rate-lookup)
14. [Algorithm C — Indian GST Split Preservation Logic](#14-algorithm-c--indian-gst-split-preservation-logic)
15. [Error Code Registry](#15-error-code-registry)
16. [Mapping Summary Matrix](#16-mapping-summary-matrix)

---

## 1. Mapping Standards & Conventions

### 1.1 Column Definitions

| Column | Description |
|---|---|
| **Mapping ID** | Unique identifier. Format: `MAP-{DOMAIN}-{NNN}` |
| **Source Entity & Field** | SAP table name and field (e.g., `ACDOCA.BELNR`) |
| **Target Entity & Attribute** | FinSight canonical model attribute (e.g., `journalEntry.documentId`) |
| **Data Type (Source → Target)** | SAP ABAP type → Java/JSON type |
| **Mandatory / Nullable** | Whether null values are permitted in the target |
| **Transformation Rule & Business Logic** | Exact formula, function, or lookup instruction |
| **Validation Rule** | Regex, range check, or referential integrity rule |
| **Error Handling / Exception Routing** | Error code and routing on failure |

### 1.2 ABAP → Java Type Mapping Reference

| ABAP Type | ABAP Description | Java / JSON Target Type |
|---|---|---|
| `CHAR(n)` | Character string | `String` |
| `NUMC(n)` | Numeric character string | `String` (zero-padded preserved) |
| `CURR(p,s)` | Currency amount | `String` (string-encoded decimal) |
| `QUAN(p,s)` | Quantity | `BigDecimal` |
| `DATS` | Date (YYYYMMDD) | `LocalDate` (ISO 8601: YYYY-MM-DD) |
| `TIMS` | Time (HHMMSS) | `LocalTime` (ISO 8601: HH:mm:ss) |
| `DEC(p,s)` | Packed decimal | `BigDecimal` |
| `INT4` | 4-byte integer | `Integer` |
| `CLNT(3)` | SAP Client | `String` (excluded from target) |
| `LAND1` | Country key | `String(2)` (ISO 3166-1 alpha-2) |

### 1.3 Fiscal Variant Reference (V3 — Indian Fiscal Year Apr-Mar)

Meridian uses SAP Fiscal Year Variant **V3** (April → March). Mapping to FinSight calendar months:

| SAP Period | Fiscal Month | Calendar Month | FinSight Code | Special Period |
|---|---|---|---|---|
| 001 | Month 1 | April | M04 | No |
| 002 | Month 2 | May | M05 | No |
| 003 | Month 3 | June | M06 | No |
| 004 | Month 4 | July | M07 | No |
| 005 | Month 5 | August | M08 | No |
| 006 | Month 6 | September | M09 | No |
| 007 | Month 7 | October | M10 | No |
| 008 | Month 8 | November | M11 | No |
| 009 | Month 9 | December | M12 | No |
| 010 | Month 10 | January | M01 | No |
| 011 | Month 11 | February | M02 | No |
| 012 | Month 12 | March | M03 | No |
| 013 | Special Period 1 | March (adj.) | M03 | Yes |
| 014 | Special Period 2 | March (adj.) | M03 | Yes |
| 015 | Special Period 3 | March (adj.) | M03 | Yes |
| 016 | Special Period 4 | March (adj.) | M03 | Yes |

### 1.4 Error Code Naming Convention

`ERR-MAP-{DOMAIN}-{NNN}` — routes to DLQ topic `sap.dlq` with error metadata attached as Kafka headers.

---

## 2. Domain 1 — General Ledger Accounting

**Source Tables:** `ACDOCA`, `BKPF`
**Target Entity:** `journalEntry`
**ODP Provider:** `0FI_GL_14`
**Mapping Count: 12 (MAP-GL-001 → MAP-GL-012)**

---

### MAP-GL-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-001 |
| **Source Entity & Field** | `ACDOCA.BELNR` + `ACDOCA.BUKRS` + `ACDOCA.GJAHR` |
| **Target Entity & Attribute** | `journalEntry.documentId` |
| **Data Type (Source → Target)** | `NUMC(10)` + `CHAR(4)` + `NUMC(4)` → `String` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | Composite key construction: `CONCAT(BUKRS, '-', GJAHR, '-', LTRIM(BELNR, '0'))`. LTRIM removes leading zeros from the 10-digit document number to produce a human-readable ID. Example: `BUKRS=1000`, `GJAHR=2026`, `BELNR=0001400000123` → `"1000-2026-1400000123"`. This composite key is the globally unique journal entry identifier within FinSight. |
| **Validation Rule** | Pattern: `^\d{4}-\d{4}-\d{1,10}$`. Min length after LTRIM: 1 digit. |
| **Error Handling / Exception Routing** | If any component field is null or empty → `ERR-MAP-GL-001` → DLQ. Alert: "Critical: documentId cannot be constructed — source record rejected." |

---

### MAP-GL-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-002 |
| **Source Entity & Field** | `ACDOCA.BUDAT` |
| **Target Entity & Attribute** | `journalEntry.postingDate` |
| **Data Type (Source → Target)** | `DATS (YYYYMMDD)` → `LocalDate (YYYY-MM-DD)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | Parse SAP DATS format string `"YYYYMMDD"` to ISO 8601 `LocalDate`. Java: `LocalDate.parse(budat, DateTimeFormatter.BASIC_ISO_DATE)`. Validate year is within [2020, 2030]. Reject `"00000000"` (SAP null date sentinel). |
| **Validation Rule** | Not null, not `"00000000"`. Year between 2020–2030. Must not be a future date beyond system date + 5 business days (allows backdated postings). |
| **Error Handling / Exception Routing** | Invalid date → `ERR-MAP-GL-002` → DLQ. Zero date (`00000000`) → `ERR-MAP-GL-002-NULL` → DLQ. |

---

### MAP-GL-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-003 |
| **Source Entity & Field** | `ACDOCA.POPER` + `ACDOCA.GJAHR` |
| **Target Entity & Attribute** | `journalEntry.fiscalPeriodCode` + `journalEntry.calendarMonthCode` + `journalEntry.isSpecialPeriod` |
| **Data Type (Source → Target)** | `NUMC(3)` + `NUMC(4)` → `String` + `String` + `Boolean` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | Indian Fiscal Variant V3 (April–March) translation. Algorithm: `IF POPER IN ['001'..'012']: calendarMonth = FISCAL_V3_MAP[POPER]; isSpecialPeriod = false; ELSE IF POPER IN ['013'..'016']: calendarMonth = 'M03'; isSpecialPeriod = true; END`. `FISCAL_V3_MAP`: `{001→M04, 002→M05, 003→M06, 004→M07, 005→M08, 006→M09, 007→M10, 008→M11, 009→M12, 010→M01, 011→M02, 012→M03}`. `fiscalPeriodCode` = zero-padded POPER (e.g., `"007"`). `fiscalYear` = GJAHR. |
| **Validation Rule** | POPER must be in range `['001'..'016']`. GJAHR must be 4-digit numeric within [2020, 2035]. |
| **Error Handling / Exception Routing** | Out-of-range POPER → `ERR-MAP-GL-003` → DLQ. |

---

### MAP-GL-004

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-004 |
| **Source Entity & Field** | `ACDOCA.HSL` + `ACDOCA.HWAER` |
| **Target Entity & Attribute** | `journalEntry.lineItem.amountInCompanyCodeCurrency.amount` + `.currency` |
| **Data Type (Source → Target)** | `CURR(23,2)` + `CHAR(5)` → `String (decimal)` + `String(3)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `HSL` = Local (Company Code) currency amount. Extract using `BigDecimal.valueOf(HSL).setScale(2, ROUND_HALF_UP).toPlainString()`. `HWAER` = Company Code currency key — trim trailing spaces, assert length = 3 (ISO 4217). For Meridian, `HWAER` is always `"INR"`. Negative values (credit amounts) preserve the minus sign: `"-125000.00"`. |
| **Validation Rule** | Amount: pattern `^-?\d+\.\d{2}$`. Currency: ISO 4217 regex `^[A-Z]{3}$`. Assert `HWAER = 'INR'` for all Meridian postings; warn if non-INR (may indicate misconfiguration). |
| **Error Handling / Exception Routing** | Null HSL → `ERR-MAP-GL-004` → DLQ. Non-INR HWAER → `ERR-MAP-GL-004-CCY` → DLQ with currency mismatch alert. |

---

### MAP-GL-005

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-005 |
| **Source Entity & Field** | `ACDOCA.WSL` + `ACDOCA.WAERS` |
| **Target Entity & Attribute** | `journalEntry.lineItem.amountInTransactionCurrency.amount` + `.currency` |
| **Data Type (Source → Target)** | `CURR(23,2)` + `CHAR(5)` → `String (decimal)` + `String(3)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `WSL` = Transaction (document) currency amount. Extract as `BigDecimal`, scale to 2 decimal places (4 places for JPY/KWD if `WAERS` dictates). `WAERS` = Transaction currency key. If `WAERS = HWAER` (same currency), then `WSL = HSL` (no conversion needed). If foreign currency (`WAERS ≠ 'INR'`), trigger Algorithm B (TCURR lookup) to compute INR equivalent and store in `HSL`. See MAP-GL-004. |
| **Validation Rule** | WSL not null. WAERS: ISO 4217 regex `^[A-Z]{3}$`. If `WAERS ≠ 'INR'`, verify exchange rate record exists in TCURR for `(WAERS, INR, BUDAT)`. |
| **Error Handling / Exception Routing** | Null WSL → `ERR-MAP-GL-005` → DLQ. Missing TCURR rate → `ERR-MAP-GL-005-FX` → DLQ (see Algorithm B fallback). |

---

### MAP-GL-006

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-006 |
| **Source Entity & Field** | `ACDOCA.RACCT` |
| **Target Entity & Attribute** | `journalEntry.lineItem.glAccount` + `journalEntry.lineItem.glAccountDescription` + `journalEntry.lineItem.scheduleIIICategory` |
| **Data Type (Source → Target)** | `CHAR(10)` → `String(10)` + `String(50)` + `String(30)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | 1. `glAccount` = RACCT (zero-padded, 10 chars). 2. `glAccountDescription` = lookup `SKA1.TXT50` where `SAKNR = RACCT AND KTOPL = 'MERI'` (Meridian Chart of Accounts). 3. `scheduleIIICategory` = lookup `ZFINSIGHT_COA_MAP.SCHEDULE_III_CAT` where `SAKNR = RACCT` — maps Meridian accounts to Schedule III of the Companies Act 2013 categories (e.g., `"PROPERTY_PLANT_EQUIPMENT"`, `"TRADE_PAYABLES"`, `"REVENUE_FROM_OPERATIONS"`). |
| **Validation Rule** | RACCT must exist in `SKA1` for chart `MERI`. Referential integrity: if account not found → reject. Schedule III category must be in the approved enum list (14 categories). |
| **Error Handling / Exception Routing** | Account not in CoA → `ERR-MAP-GL-006` → DLQ. Missing Schedule III mapping → `ERR-MAP-GL-006-COA` → DLQ with alert to Finance team. |

---

### MAP-GL-007

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-007 |
| **Source Entity & Field** | `ACDOCA.DRCRK` |
| **Target Entity & Attribute** | `journalEntry.lineItem.debitCreditCode` + `journalEntry.lineItem.signedAmount` |
| **Data Type (Source → Target)** | `CHAR(1)` → `String(1)` + `String (decimal)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `DRCRK` = `'S'` (Soll/Debit) or `'H'` (Haben/Credit). Pass-through as-is: `debitCreditCode = DRCRK`. Compute `signedAmount`: `IF DRCRK = 'S' THEN signedAmount = ABS(HSL); ELSE signedAmount = NEGATE(ABS(HSL)); END`. This ensures debits are positive and credits are negative in FinSight's analytical model for balance sheet equation validation. |
| **Validation Rule** | `DRCRK` must be exactly `'S'` or `'H'`. No other values permitted. |
| **Error Handling / Exception Routing** | Invalid DRCRK value → `ERR-MAP-GL-007` → DLQ. |

---

### MAP-GL-008

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-008 |
| **Source Entity & Field** | `ACDOCA.BLART` |
| **Target Entity & Attribute** | `journalEntry.documentType` + `journalEntry.documentTypeDescription` + `journalEntry.documentCategory` |
| **Data Type (Source → Target)** | `CHAR(2)` → `String(2)` + `String(40)` + `String(20)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | Pass-through: `documentType = BLART`. Lookup description from `T003T.LTEXT WHERE BLART = ACDOCA.BLART AND SPRAS = 'EN'`. Classify into FinSight document categories using lookup table `ZFINSIGHT_DOCTYPE_MAP`: `{SA→GENERAL_LEDGER, KR→VENDOR_INVOICE, KZ→VENDOR_PAYMENT, DR→CUSTOMER_INVOICE, DZ→CUSTOMER_PAYMENT, RE→GOODS_RECEIPT, AA→ASSET_POSTING, ZP→INTERCOMPANY}`. Unknown types → `documentCategory = 'OTHER'`. |
| **Validation Rule** | BLART length = 1–2 chars. Description lookup: warn (not reject) if T003T entry missing. |
| **Error Handling / Exception Routing** | Null BLART → `ERR-MAP-GL-008` → DLQ. Unknown BLART not in lookup → log WARNING, set `documentCategory = 'OTHER'`, continue processing. |

---

### MAP-GL-009

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-009 |
| **Source Entity & Field** | `BKPF.STBLG` + `BKPF.STJAH` |
| **Target Entity & Attribute** | `journalEntry.isReversalDocument` + `journalEntry.reversalOfDocumentId` |
| **Data Type (Source → Target)** | `NUMC(10)` + `NUMC(4)` → `Boolean` + `String` |
| **Mandatory / Nullable** | `isReversalDocument`: Mandatory; `reversalOfDocumentId`: Nullable |
| **Transformation Rule & Business Logic** | `BKPF.STBLG` = Reversal document number. `BKPF.STJAH` = Reversal document fiscal year. Logic: `IF STBLG IS NOT NULL AND STBLG ≠ '0000000000' THEN isReversalDocument = true; reversalOfDocumentId = CONCAT(BUKRS, '-', STJAH, '-', LTRIM(STBLG, '0')); ELSE isReversalDocument = false; reversalOfDocumentId = null; END`. Join `BKPF` on `(BUKRS, GJAHR, BELNR)` matching ACDOCA header. |
| **Validation Rule** | If `isReversalDocument = true`, assert `reversalOfDocumentId` follows documentId pattern `^\d{4}-\d{4}-\d{1,10}$`. Referential check: reversed document must exist in FinSight GL store or be queued for ingestion. |
| **Error Handling / Exception Routing** | BKPF join failure (header not found) → `ERR-MAP-GL-009` → Warning log, continue with `isReversalDocument = false`. Unresolvable reversal reference → `ERR-MAP-GL-009-REF` → flag for EoD reconciliation. |

---

### MAP-GL-010

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-010 |
| **Source Entity & Field** | `ACDOCA.PRCTR` |
| **Target Entity & Attribute** | `journalEntry.lineItem.profitCenterId` + `journalEntry.lineItem.profitCentreDescription` |
| **Data Type (Source → Target)** | `CHAR(10)` → `String(10)` + `String(40)` |
| **Mandatory / Nullable** | Nullable (not all accounts have PC assignment) |
| **Transformation Rule & Business Logic** | Pass-through: `profitCenterId = TRIM(PRCTR)`. Lookup description: `CEPCT.MCTXT WHERE PRCTR = ACDOCA.PRCTR AND KOKRS = ACDOCA.KOKRS AND SPRAS = 'EN'`. If PRCTR is blank/null → set `profitCenterId = null`, `profitCentreDescription = null`. Validate PC exists in `CEPC` master (referential integrity). |
| **Validation Rule** | If non-null: PRCTR must exist in `CEPC` for `KOKRS = 'MFGL'` (Meridian Controlling Area). Max length 10 chars. |
| **Error Handling / Exception Routing** | PC not in CEPC master → `ERR-MAP-GL-010` → Warning + flag for master data sync via DST-005. Processing continues with null PC. |

---

### MAP-GL-011

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-011 |
| **Source Entity & Field** | `ACDOCA.KOSTL` |
| **Target Entity & Attribute** | `journalEntry.lineItem.costCentreId` + `journalEntry.lineItem.costCentreHierarchyPath` |
| **Data Type (Source → Target)** | `CHAR(10)` → `String(10)` + `String(255)` |
| **Mandatory / Nullable** | Nullable (cost-relevant postings only) |
| **Transformation Rule & Business Logic** | Pass-through: `costCentreId = TRIM(KOSTL)`. `costCentreHierarchyPath` = invoke Algorithm A (hierarchy flattening) using `KOSTL` as leaf node key against `SETNODE/SETLEAF` for set `'MERI_CC_H1'` — returns `"L1/L2/L3/L4/L5/L6/L7"` path string. Result cached in Redis (TTL 24h). If KOSTL null/blank → both fields null. |
| **Validation Rule** | If non-null: KOSTL must exist in `CSKS` for `KOKRS = 'MFGL'` and validity date within `(DATAB ≤ BUDAT ≤ DATBI)`. |
| **Error Handling / Exception Routing** | CC not in CSKS → `ERR-MAP-GL-011` → Warning + flag for master data sync via DST-004. Hierarchy path resolution failure → `ERR-MAP-GL-011-HIER` → set path to null, log, continue. |

---

### MAP-GL-012

| Column | Value |
|---|---|
| **Mapping ID** | MAP-GL-012 |
| **Source Entity & Field** | `ACDOCA.RASSC` |
| **Target Entity & Attribute** | `journalEntry.intercompanyPartnerCode` + `journalEntry.isIntercompany` |
| **Data Type (Source → Target)** | `CHAR(6)` → `String(6)` + `Boolean` |
| **Mandatory / Nullable** | `isIntercompany`: Mandatory; `intercompanyPartnerCode`: Nullable |
| **Transformation Rule & Business Logic** | `RASSC` = Trading partner (intercompany company code). `IF RASSC IS NOT NULL AND RASSC ≠ '' THEN isIntercompany = true; intercompanyPartnerCode = TRIM(RASSC); ELSE isIntercompany = false; intercompanyPartnerCode = null; END`. Intercompany records are routed to dedicated Kafka topic `sap.intercompany` with single-partition ordering (see D1 §5.3). |
| **Validation Rule** | If non-null: RASSC must be a valid company code in `T001` table. Must differ from `BUKRS` (cannot be self-intercompany). |
| **Error Handling / Exception Routing** | RASSC = BUKRS (self-IC) → `ERR-MAP-GL-012` → DLQ with data quality alert. Unknown partner code → `ERR-MAP-GL-012-REF` → route to IC reconciliation hold queue. |

---

## 3. Domain 2 — Accounts Payable

**Source Tables:** `BSIK`, `BSAK`, `BKPF`, `LFA1`, `LFC1`, `WITH_ITEM`
**Target Entity:** `apItem`
**ODP Provider:** `0FI_AP_4`
**Mapping Count: 8 (MAP-AP-001 → MAP-AP-008)**

---

### MAP-AP-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AP-001 |
| **Source Entity & Field** | `BSIK.LIFNR` + `LFA1.NAME1` |
| **Target Entity & Attribute** | `apItem.vendorId` + `apItem.vendorName` |
| **Data Type (Source → Target)** | `CHAR(10)` + `CHAR(35)` → `String` + `String` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | Vendor ID normalization: `vendorId = LTRIM(LIFNR, '0')` — strip leading zeros for FinSight canonical ID. Join `LFA1` on `LIFNR` to resolve `NAME1`. `vendorName = TRIM(NAME1)`. Build compound display name: if `LFA1.NAME2` non-null, append `' ' + TRIM(NAME2)`. |
| **Validation Rule** | LIFNR must exist in `LFA1`. `NAME1` not null. Vendor must not be marked for deletion (`LFA1.LOEVM ≠ 'X'`). |
| **Error Handling / Exception Routing** | Vendor not in LFA1 → `ERR-MAP-AP-001` → DLQ. Vendor deletion-flagged → `ERR-MAP-AP-001-DEL` → Warning log, include `isDeleted: true` flag in payload. |

---

### MAP-AP-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AP-002 |
| **Source Entity & Field** | `LFA1.STCD3` |
| **Target Entity & Attribute** | `apItem.vendorGstin` |
| **Data Type (Source → Target)** | `CHAR(20)` → `String(15)` |
| **Mandatory / Nullable** | Nullable (vendors exempt from GST may not have GSTIN) |
| **Transformation Rule & Business Logic** | `LFA1.STCD3` stores the Indian GSTIN in SAP. `vendorGstin = UPPER(TRIM(STCD3))`. If blank → null. The GSTIN must match the state code of the vendor's registered address (`LFA1.REGIO` → first 2 digits of GSTIN). State code lookup: `ZGSTIN_STATE_MAP[REGIO]` → 2-digit GSTIN state prefix. Validate structure per GST Council format. |
| **Validation Rule** | Regex: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`. State code prefix (first 2 digits) must match `ZGSTIN_STATE_MAP[LFA1.REGIO]`. |
| **Error Handling / Exception Routing** | Invalid GSTIN format → `ERR-MAP-AP-002` → Warning + `isGstinValid: false` flag set. Input tax credit eligibility set to `false` automatically. Alert to AP team for vendor master correction. |

---

### MAP-AP-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AP-003 |
| **Source Entity & Field** | `BSIK.ZFBDT` + `BSIK.ZBD1T` + `BSIK.ZBD2T` + `BSIK.ZTERM` |
| **Target Entity & Attribute** | `apItem.baselineDate` + `apItem.netDueDate` + `apItem.cashDiscountDate1` + `apItem.paymentTermsKey` |
| **Data Type (Source → Target)** | `DATS` × 3 + `CHAR(4)` → `LocalDate` × 3 + `String(4)` |
| **Mandatory / Nullable** | `baselineDate`: Mandatory; others: Nullable |
| **Transformation Rule & Business Logic** | `baselineDate = parse_DATS(ZFBDT)`. `netDueDate = baselineDate + ZBD1T` (days). If `ZBD1T = 0`, apply payment terms lookup: `T052.ZTAG1` where `ZTERM = BSIK.ZTERM`. `cashDiscountDate1 = baselineDate + ZBD2T` (if ZBD2T > 0). `paymentTermsKey = BSIK.ZTERM`. Example: `ZTERM='NT30'`, `ZFBDT=2026-09-25`, `ZBD1T=30` → `netDueDate = 2026-10-25`. |
| **Validation Rule** | `baselineDate` not null, not `00000000`. `netDueDate ≥ baselineDate`. `cashDiscountDate1 < netDueDate` (if non-null). |
| **Error Handling / Exception Routing** | Null `ZFBDT` → `ERR-MAP-AP-003` → DLQ. `netDueDate < baselineDate` → `ERR-MAP-AP-003-DATE` → DLQ with date logic alert. |

---

### MAP-AP-004

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AP-004 |
| **Source Entity & Field** | `BSIK.DMBTR` + `BSIK.WAERS` + `BSIK.BUDAT` (extraction timestamp) |
| **Target Entity & Attribute** | `apItem.outstandingAmount` + `apItem.ageingBucket` + `apItem.daysOverdue` |
| **Data Type (Source → Target)** | `CURR(13,2)` + `CHAR(5)` + `DATS` → `String` + `String (enum)` + `Integer` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `outstandingAmount.amount = ABS(DMBTR).toPlainString()`. `outstandingAmount.currency = TRIM(WAERS)`. Ageing computation: `daysOverdue = MAX(0, DATEDIFF(extractionDate, netDueDate))` where `netDueDate` from MAP-AP-003. Ageing bucket derivation: `IF daysOverdue = 0 AND extractionDate < netDueDate THEN 'CURRENT'; ELSE IF daysOverdue BETWEEN 1 AND 30 THEN 'OVERDUE_1_30'; ELSE IF daysOverdue BETWEEN 31 AND 60 THEN 'OVERDUE_31_60'; ELSE IF daysOverdue BETWEEN 61 AND 90 THEN 'OVERDUE_61_90'; ELSE IF daysOverdue BETWEEN 91 AND 180 THEN 'OVERDUE_91_180'; ELSE 'OVERDUE_180_PLUS'; END`. |
| **Validation Rule** | `DMBTR ≥ 0`. `daysOverdue ≥ 0`. `ageingBucket` in enum set. |
| **Error Handling / Exception Routing** | Negative DMBTR (unusual for AP) → `ERR-MAP-AP-004-NEG` → Warning flag, take ABS, include `rawAmount` for audit. |

---

### MAP-AP-005

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AP-005 |
| **Source Entity & Field** | `BSIK.ZLSPR` |
| **Target Entity & Attribute** | `apItem.paymentBlock` + `apItem.paymentBlockDescription` |
| **Data Type (Source → Target)** | `CHAR(1)` → `String(1)` + `String(30)` |
| **Mandatory / Nullable** | Nullable (blank = not blocked) |
| **Transformation Rule & Business Logic** | `ZLSPR` = Payment block indicator. `paymentBlock = TRIM(ZLSPR)` (null if blank). Lookup description from `T008T.TEXT1` where `ZLSPR = BSIK.ZLSPR AND SPRAS = 'EN'`. FinSight payment block codes: `{blank→null/'FREE', 'A'→'FREE_FOR_PAYMENT', 'R'→'BLOCKED_MANUAL', 'B'→'BLOCKED_CREDIT_MEMO', 'Z'→'BLOCKED_AUDIT'}`. Derive boolean `isPaymentBlocked = (paymentBlock IS NOT NULL)`. |
| **Validation Rule** | ZLSPR value must be in T008 or blank. Max 1 character. |
| **Error Handling / Exception Routing** | Unknown block code → `ERR-MAP-AP-005` → Warning, set `paymentBlockDescription = 'UNKNOWN'`, continue. |

---

### MAP-AP-006

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AP-006 |
| **Source Entity & Field** | `WITH_ITEM.WITHT` + `WITH_ITEM.WT_WITHCD` + `WITH_ITEM.WT_QSSHB` + `WITH_ITEM.WT_QBSHB` + `WITH_ITEM.WAERS` |
| **Target Entity & Attribute** | `apItem.withholdingTax.section` + `.taxType` + `.taxAmount` + `.baseAmount` + `.currency` |
| **Data Type (Source → Target)** | `CHAR(2)` + `CHAR(2)` + `CURR(13,2)` + `CURR(13,2)` + `CHAR(5)` → `String` × 5 |
| **Mandatory / Nullable** | Nullable (only for TDS-applicable vendors) |
| **Transformation Rule & Business Logic** | Join `WITH_ITEM` on `(BUKRS, BELNR, GJAHR, BUZEI)`. `WITHT` = Withholding tax type (maps to IT Section: `C1→194C, J1→194J, H1→194H, Q1→194Q, I1→195`). `WT_WITHCD` = TDS code. `WT_QSSHB` = TDS base amount. `WT_QBSHB` = TDS tax amount (already calculated by SAP). `taxRate = ROUND((WT_QBSHB / WT_QSSHB) * 100, 2)`. Validate: calculated `taxRate` must match declared rate in `T059Z.PROZS` for the withholding code. `totalTdsAmount = WT_QBSHB + surcharge + cess` (surcharge and cess from `WITH_ITEM.WT_SURH` and `WITH_ITEM.WT_CESH`). |
| **Validation Rule** | `WT_QSSHB > 0`. `WT_QBSHB ≤ WT_QSSHB`. `taxRate` within [0, 30]%. Sum check: `taxAmount + surcharge + cess = totalTdsAmount`. |
| **Error Handling / Exception Routing** | TDS sum mismatch → `ERR-MAP-AP-006` → DLQ with tax integrity alert. Missing TDS record for mandatory-TDS vendor → `ERR-MAP-AP-006-MISS` → DLQ + alert to Tax team. |

---

### MAP-AP-007

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AP-007 |
| **Source Entity & Field** | `LFA1.STCD2` + `LFA1.LOEVM` |
| **Target Entity & Attribute** | `apItem.vendorPan` + `apItem.isVendorDeleted` |
| **Data Type (Source → Target)** | `CHAR(11)` + `CHAR(1)` → `String(10)` + `Boolean` |
| **Mandatory / Nullable** | `vendorPan`: Nullable; `isVendorDeleted`: Mandatory |
| **Transformation Rule & Business Logic** | `LFA1.STCD2` = PAN in SAP Indian tax configuration. `vendorPan = UPPER(TRIM(STCD2))`. If blank/null → null. `isVendorDeleted = (LOEVM = 'X')`. If PAN null and vendor is TDS-applicable (`WITH_ITEM` exists with rate < 20%) → alert: "Section 206AA: higher TDS rate of 20% should apply — PAN missing." |
| **Validation Rule** | PAN regex: `^[A-Z]{5}[0-9]{4}[A-Z]{1}$`. Must be exactly 10 characters. |
| **Error Handling / Exception Routing** | Invalid PAN format → `ERR-MAP-AP-007` → Warning + `isPanValid: false`. Missing PAN for TDS vendor → `ERR-MAP-AP-007-206AA` → Alert to Tax team; set `higherTdsRateApplicable: true`. |

---

### MAP-AP-008

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AP-008 |
| **Source Entity & Field** | `BSAK.AUGDT` + `BSAK.AUGBL` |
| **Target Entity & Attribute** | `apItem.clearingDate` + `apItem.clearingDocument` + `apItem.isCleared` |
| **Data Type (Source → Target)** | `DATS` + `NUMC(10)` → `LocalDate` + `String` + `Boolean` |
| **Mandatory / Nullable** | Nullable (`BSAK` only; `BSIK` records have no clearing) |
| **Transformation Rule & Business Logic** | Source split: open items come from `BSIK`; cleared items from `BSAK`. `IF record FROM BSAK: isCleared = true; clearingDate = parse_DATS(AUGDT); clearingDocument = CONCAT(BUKRS, '-', GJAHR, '-', LTRIM(AUGBL,'0')); ELSE isCleared = false; clearingDate = null; clearingDocument = null; END`. |
| **Validation Rule** | If `isCleared = true`: `clearingDate` must not be null and must be `≥ postingDate`. |
| **Error Handling / Exception Routing** | `clearingDate < postingDate` → `ERR-MAP-AP-008-DATE` → DLQ with date integrity alert. |

---

## 4. Domain 3 — Accounts Receivable

**Source Tables:** `BSID`, `BSAD`, `BKPF`, `KNA1`, `KNB1`, `KNKK`
**Target Entity:** `arItem`
**ODP Provider:** `0FI_AR_4`
**Mapping Count: 8 (MAP-AR-001 → MAP-AR-008)**

---

### MAP-AR-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AR-001 |
| **Source Entity & Field** | `BSID.KUNNR` + `KNA1.NAME1` + `KNA1.LAND1` |
| **Target Entity & Attribute** | `arItem.customerId` + `arItem.customerName` + `arItem.countryCode` |
| **Data Type (Source → Target)** | `CHAR(10)` + `CHAR(35)` + `LAND1(2)` → `String` + `String` + `String(2)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `customerId = LTRIM(KUNNR, '0')`. Join `KNA1` on `KUNNR` for `NAME1`, `LAND1`. `customerName = TRIM(NAME1)`. `countryCode = TRIM(LAND1)` (ISO 3166-1 alpha-2). |
| **Validation Rule** | KUNNR must exist in `KNA1`. NAME1 not null. LAND1 must be valid ISO 3166-1 alpha-2 code. |
| **Error Handling / Exception Routing** | Customer not in KNA1 → `ERR-MAP-AR-001` → DLQ. |

---

### MAP-AR-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AR-002 |
| **Source Entity & Field** | `KNKK.KLIMK` + `KNKK.SKFOR` + `KNB1.BUKRS` |
| **Target Entity & Attribute** | `arItem.creditLimit` + `arItem.creditExposure` + `arItem.creditUtilisationPct` |
| **Data Type (Source → Target)** | `CURR(15,2)` + `CURR(15,2)` + (computed) → `String` + `String` + `String(6)` |
| **Mandatory / Nullable** | Nullable (not all customers have credit limits) |
| **Transformation Rule & Business Logic** | Join `KNKK` on `(KUNNR, KKBER)` where `KKBER` = Meridian credit control area. `creditLimit = KLIMK.toPlainString()`. `creditExposure = SKFOR.toPlainString()` (current exposure: open AR + SD open orders). `creditUtilisationPct = ROUND((SKFOR / KLIMK) * 100, 2)` (as string, e.g., `"87.43"`). If `KLIMK = 0` → `creditLimit = null`, `creditUtilisationPct = null`. |
| **Validation Rule** | `KLIMK ≥ 0`. `SKFOR ≥ 0`. `creditUtilisationPct ∈ [0, 999.99]` (>100% = overlimit). |
| **Error Handling / Exception Routing** | `SKFOR > KLIMK * 1.2` (>120% utilisation) → `ERR-MAP-AR-002-OVR` → Warning + alert to Credit Control team. |

---

### MAP-AR-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AR-003 |
| **Source Entity & Field** | `BSID.MANST` |
| **Target Entity & Attribute** | `arItem.dunningLevel` + `arItem.dunningLevelDescription` |
| **Data Type (Source → Target)** | `NUMC(1)` → `Integer` + `String(30)` |
| **Mandatory / Nullable** | Nullable (0 = not dunned) |
| **Transformation Rule & Business Logic** | `dunningLevel = INT(MANST)`. Description lookup: `{0→'Not Dunned', 1→'First Notice', 2→'Second Notice', 3→'Third Notice (Final)', 4→'Legal Collection'}`. If `dunningLevel ≥ 3` → set `isLegalRiskFlag = true` in target payload. |
| **Validation Rule** | `MANST IN [0, 1, 2, 3, 4]`. Values > 4 unsupported by Meridian dunning config. |
| **Error Handling / Exception Routing** | `MANST > 4` → `ERR-MAP-AR-003` → Warning, cap at 4, log. |

---

### MAP-AR-004

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AR-004 |
| **Source Entity & Field** | `BSID.DMBTR` + `BSID.WAERS` + `BSID.ZFBDT` + `BSID.ZBD1T` |
| **Target Entity & Attribute** | `arItem.outstandingAmount` + `arItem.netDueDate` + `arItem.ageingBucket` + `arItem.daysOverdue` |
| **Data Type (Source → Target)** | `CURR(13,2)` + `CHAR(5)` + `DATS` + `NUMC(3)` → `String` + `LocalDate` + `String` + `Integer` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | AR ageing uses same bucket logic as AP (MAP-AP-004) but from customer perspective. `outstandingAmount.amount = ABS(DMBTR).toPlainString()`. `netDueDate = parse_DATS(ZFBDT) + ZBD1T` (days). Ageing bucket: same 6-tier enum as AP. `daysOverdue = MAX(0, DATEDIFF(extractionDate, netDueDate))`. Derive DSO (Days Sales Outstanding) contribution per line item for portfolio-level DSO calculation by FinSight. |
| **Validation Rule** | Same as MAP-AP-004 with currency check. |
| **Error Handling / Exception Routing** | Same routing as MAP-AP-004: `ERR-MAP-AR-004`. |

---

### MAP-AR-005

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AR-005 |
| **Source Entity & Field** | `BSAD.AUGDT` + `BSAD.AUGBL` + `BSAD.ZUONR` |
| **Target Entity & Attribute** | `arItem.clearingDate` + `arItem.clearingDocument` + `arItem.invoiceReference` |
| **Data Type (Source → Target)** | `DATS` + `NUMC(10)` + `CHAR(18)` → `LocalDate` + `String` + `String` |
| **Mandatory / Nullable** | Nullable (`BSAD` cleared items only) |
| **Transformation Rule & Business Logic** | Same clearing logic as MAP-AP-008 applied to AR. `isCleared = (record from BSAD)`. `invoiceReference = TRIM(ZUONR)` (assignment field used as invoice reference in Meridian's AR config). |
| **Validation Rule** | `clearingDate ≥ postingDate` if non-null. |
| **Error Handling / Exception Routing** | Date inversion → `ERR-MAP-AR-005` → DLQ. |

---

### MAP-AR-006

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AR-006 |
| **Source Entity & Field** | `KNA1.STCD3` |
| **Target Entity & Attribute** | `arItem.customerGstin` + `arItem.gstRegistrationStatus` |
| **Data Type (Source → Target)** | `CHAR(20)` → `String(15)` + `String(20)` |
| **Mandatory / Nullable** | Nullable |
| **Transformation Rule & Business Logic** | Same GSTIN extraction and validation as MAP-AP-002. `gstRegistrationStatus`: derive from GSTIN presence: `IF GSTIN valid → 'REGISTERED'; IF GSTIN null → 'UNREGISTERED'; IF GSTIN format invalid → 'INVALID'`. AR invoices to unregistered customers: GST TCS (Tax Collected at Source) may apply — set `isTcsApplicable` flag. |
| **Validation Rule** | Same GSTIN regex as MAP-AP-002. |
| **Error Handling / Exception Routing** | Same as MAP-AP-002: `ERR-MAP-AR-006`. |

---

### MAP-AR-007

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AR-007 |
| **Source Entity & Field** | `BSID.ZTERM` |
| **Target Entity & Attribute** | `arItem.paymentTermsKey` + `arItem.paymentTermsDescription` + `arItem.cashDiscountPct` |
| **Data Type (Source → Target)** | `CHAR(4)` → `String(4)` + `String(30)` + `String(5)` |
| **Mandatory / Nullable** | Nullable |
| **Transformation Rule & Business Logic** | `paymentTermsKey = TRIM(ZTERM)`. Lookup from `T052.ZTAG1` (net days) and `T052.ZPRZ1` (discount %). `paymentTermsDescription` from `T052T.TEXT1 WHERE ZTERM = BSID.ZTERM AND SPRAS = 'EN'`. `cashDiscountPct = T052.ZPRZ1.toPlainString()`. |
| **Validation Rule** | ZTERM must exist in `T052` if non-null. |
| **Error Handling / Exception Routing** | Unknown ZTERM → `ERR-MAP-AR-007` → Warning, set description to `'UNKNOWN'`, continue. |

---

### MAP-AR-008

| Column | Value |
|---|---|
| **Mapping ID** | MAP-AR-008 |
| **Source Entity & Field** | `BSID.BVTYP` + `BSID.REBZG` + `BSID.REBZJ` |
| **Target Entity & Attribute** | `arItem.partnerBankType` + `arItem.baselineDocumentId` + `arItem.isDownPayment` |
| **Data Type (Source → Target)** | `CHAR(4)` + `NUMC(10)` + `NUMC(4)` → `String` + `String` + `Boolean` |
| **Mandatory / Nullable** | Nullable |
| **Transformation Rule & Business Logic** | `partnerBankType = TRIM(BVTYP)`. Invoice/down-payment linkage: `IF REBZG IS NOT NULL: baselineDocumentId = CONCAT(BUKRS, '-', REBZJ, '-', LTRIM(REBZG,'0')); ELSE baselineDocumentId = null; END`. `isDownPayment = (BLART IN ['DA', 'DZ'] AND BVTYP = 'DOWN')`. |
| **Validation Rule** | If `baselineDocumentId` non-null, referenced document must exist or be in-flight. |
| **Error Handling / Exception Routing** | Unresolved baseline doc → `ERR-MAP-AR-008` → Warning flag, continue. |

---

## 5. Domain 4 — Cost Centre Accounting

**Source Tables:** `CSKS`, `CSKT`, `ACDOCA` (CO segment)
**Target Entity:** `costCentre`
**ODP Provider:** `0CO_CCA_3`
**Mapping Count: 6 (MAP-CO-001 → MAP-CO-006)**

---

### MAP-CO-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-CO-001 |
| **Source Entity & Field** | `CSKS.KOSTL` + `CSKS.KOKRS` |
| **Target Entity & Attribute** | `costCentre.costCentreId` + `costCentre.controllingArea` |
| **Data Type (Source → Target)** | `CHAR(10)` + `CHAR(4)` → `String` + `String(4)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `costCentreId = TRIM(KOSTL)`. `controllingArea = TRIM(KOKRS)`. Assert `KOKRS = 'MFGL'` (Meridian's single controlling area). Composite key for FinSight master: `CONCAT(KOKRS, '-', TRIM(KOSTL))` stored as `costCentreKey`. |
| **Validation Rule** | `KOSTL` not null. `KOKRS = 'MFGL'`. |
| **Error Handling / Exception Routing** | Wrong controlling area → `ERR-MAP-CO-001` → DLQ. |

---

### MAP-CO-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-CO-002 |
| **Source Entity & Field** | `CSKT.MCTXT` (with `SPRAS = 'EN'`) |
| **Target Entity & Attribute** | `costCentre.costCentreDescription` |
| **Data Type (Source → Target)** | `CHAR(40)` → `String(40)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `costCentreDescription = TRIM(MCTXT)` from `CSKT` where `KOKRS = 'MFGL' AND KOSTL = CSKS.KOSTL AND SPRAS = 'EN'`. Fallback language: if English not available → use `SPRAS = 'DE'` → transliterate to English. |
| **Validation Rule** | Description not null, min length 1. |
| **Error Handling / Exception Routing** | No description found → `ERR-MAP-CO-002` → Warning, set `costCentreDescription = costCentreId`, continue. |

---

### MAP-CO-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-CO-003 |
| **Source Entity & Field** | `CSKS.DATAB` + `CSKS.DATBI` |
| **Target Entity & Attribute** | `costCentre.validFrom` + `costCentre.validTo` |
| **Data Type (Source → Target)** | `DATS` + `DATS` → `LocalDate` + `LocalDate` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `validFrom = parse_DATS(DATAB)`. `validTo = parse_DATS(DATBI)`. SAP uses `DATBI = '99991231'` for open-ended validity → map to ISO representation `"9999-12-31"`. Derive `isActive = (DATAB ≤ TODAY ≤ DATBI)`. |
| **Validation Rule** | `validFrom ≤ validTo`. `validFrom` must be a valid date. |
| **Error Handling / Exception Routing** | `validFrom > validTo` → `ERR-MAP-CO-003` → DLQ. |

---

### MAP-CO-004

| Column | Value |
|---|---|
| **Mapping ID** | MAP-CO-004 |
| **Source Entity & Field** | `CSKS.PRCTR` |
| **Target Entity & Attribute** | `costCentre.linkedProfitCentreId` |
| **Data Type (Source → Target)** | `CHAR(10)` → `String(10)` |
| **Mandatory / Nullable** | Nullable |
| **Transformation Rule & Business Logic** | `linkedProfitCentreId = TRIM(PRCTR)`. Referential check: must exist in `CEPC` table for `KOKRS = 'MFGL'`. This linkage enables FinSight to automatically associate CC cost data to the parent PC segment for P&L attribution. |
| **Validation Rule** | If non-null: PRCTR must exist in CEPC. |
| **Error Handling / Exception Routing** | Dangling PC reference → `ERR-MAP-CO-004` → Warning + master data alert. |

---

### MAP-CO-005

| Column | Value |
|---|---|
| **Mapping ID** | MAP-CO-005 |
| **Source Entity & Field** | `CSKS.KOSAR` |
| **Target Entity & Attribute** | `costCentre.costCentreCategory` + `costCentre.costCentreCategoryDescription` |
| **Data Type (Source → Target)** | `CHAR(1)` → `String(1)` + `String(30)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `KOSAR` = Cost Centre Category. Pass-through. Lookup description from static map: `{P→'Production', A→'Administration', S→'Sales & Distribution', F→'Research & Development', H→'Auxiliary (Helper)', V→'Overhead', M→'Material Management', L→'Plant Maintenance'}`. |
| **Validation Rule** | `KOSAR` in `[P, A, S, F, H, V, M, L]`. |
| **Error Handling / Exception Routing** | Unknown category → `ERR-MAP-CO-005` → Warning, set description = `'OTHER'`. |

---

### MAP-CO-006

| Column | Value |
|---|---|
| **Mapping ID** | MAP-CO-006 |
| **Source Entity & Field** | `ACDOCA.KSTAR` + `ACDOCA.KOSTL` + `ACDOCA.KSL` |
| **Target Entity & Attribute** | `costCentreActual.costElementId` + `.costCentreId` + `.actualAmountCC` |
| **Data Type (Source → Target)** | `CHAR(10)` + `CHAR(10)` + `CURR(23,2)` → `String` + `String` + `String` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `costElementId = TRIM(KSTAR)`. `costCentreId = TRIM(KOSTL)`. `actualAmountCC.amount = KSL.toPlainString()` (company code currency amount for CO). `actualAmountCC.currency = 'INR'` (Meridian CC currency). Cost element lookup: `CSKA.KSTAR` for description. This forms the actual cost posting line in FinSight's cost centre report. |
| **Validation Rule** | `KSTAR` must exist in `CSKA` for `KOKRS = 'MFGL'`. `KSL` not null. |
| **Error Handling / Exception Routing** | Unknown cost element → `ERR-MAP-CO-006` → DLQ. |

---

## 6. Domain 5 — Profit Centre Accounting

**Source Tables:** `CEPC`, `CEPCT`, `ACDOCP`
**Target Entity:** `profitCentre`
**ODP Provider:** `0EC_PCA_3`
**Mapping Count: 4 (MAP-PC-001 → MAP-PC-004)**

---

### MAP-PC-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-PC-001 |
| **Source Entity & Field** | `CEPC.PRCTR` + `CEPC.KOKRS` |
| **Target Entity & Attribute** | `profitCentre.profitCentreId` + `profitCentre.controllingArea` |
| **Data Type (Source → Target)** | `CHAR(10)` + `CHAR(4)` → `String(10)` + `String(4)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `profitCentreId = TRIM(PRCTR)`. `controllingArea = TRIM(KOKRS)`. Assert `KOKRS = 'MFGL'`. Composite master key: `CONCAT(KOKRS, '-', TRIM(PRCTR))`. |
| **Validation Rule** | Not null. `KOKRS = 'MFGL'`. |
| **Error Handling / Exception Routing** | Wrong KOKRS → `ERR-MAP-PC-001` → DLQ. |

---

### MAP-PC-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-PC-002 |
| **Source Entity & Field** | `CEPCT.MCTXT` (with `SPRAS = 'EN'`) + `CEPC.SEGMENT` |
| **Target Entity & Attribute** | `profitCentre.description` + `profitCentre.segment` + `profitCentre.segmentDescription` |
| **Data Type (Source → Target)** | `CHAR(40)` + `CHAR(10)` → `String(40)` + `String(10)` + `String(30)` |
| **Mandatory / Nullable** | `description`: Mandatory; `segment`: Nullable |
| **Transformation Rule & Business Logic** | `description = TRIM(MCTXT)`. `segment = TRIM(CEPC.SEGMENT)`. Segment classification lookup (Meridian-specific): `{SEG_AUTO→'Automotive', SEG_AERO→'Aerospace', SEG_INDUST→'Industrial', SEG_INFRA→'Infrastructure', SEG_CONS→'Consumer Goods'}`. `segmentDescription` = lookup result. |
| **Validation Rule** | `MCTXT` not null. SEGMENT must be in approved segment list if non-null. |
| **Error Handling / Exception Routing** | Unknown segment → `ERR-MAP-PC-002` → Warning, set `segmentDescription = 'UNCLASSIFIED'`. |

---

### MAP-PC-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-PC-003 |
| **Source Entity & Field** | `CEPC.DATAB` + `CEPC.DATBI` + `CEPC.LOEVM` |
| **Target Entity & Attribute** | `profitCentre.validFrom` + `profitCentre.validTo` + `profitCentre.isActive` + `profitCentre.isDeletionFlagged` |
| **Data Type (Source → Target)** | `DATS` + `DATS` + `CHAR(1)` → `LocalDate` + `LocalDate` + `Boolean` + `Boolean` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `validFrom = parse_DATS(DATAB)`. `validTo = parse_DATS(DATBI)` (9999-12-31 for open-ended). `isActive = (DATAB ≤ TODAY ≤ DATBI AND LOEVM ≠ 'X')`. `isDeletionFlagged = (LOEVM = 'X')`. |
| **Validation Rule** | `validFrom ≤ validTo`. |
| **Error Handling / Exception Routing** | Date inversion → `ERR-MAP-PC-003` → DLQ. |

---

### MAP-PC-004

| Column | Value |
|---|---|
| **Mapping ID** | MAP-PC-004 |
| **Source Entity & Field** | `ACDOCP.KSL` + `ACDOCP.PRCTR` + `ACDOCP.RACCT` + `ACDOCP.POPER` |
| **Target Entity & Attribute** | `profitCentreActual.actualAmount` + `.profitCentreId` + `.glAccount` + `.fiscalPeriod` |
| **Data Type (Source → Target)** | `CURR(23,2)` + `CHAR(10)` + `CHAR(10)` + `NUMC(3)` → `String` + `String` + `String` + `String` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `ACDOCP` = Profit Centre Document table. `actualAmount.amount = KSL.toPlainString()`. Signed per debit/credit code. `profitCentreId = TRIM(PRCTR)`. `glAccount = TRIM(RACCT)`. `fiscalPeriod` mapped via V3 logic (MAP-GL-003). Forms the basis of FinSight's segment P&L report. |
| **Validation Rule** | `KSL` not null. `PRCTR` must exist in CEPC. `RACCT` must exist in SKA1. |
| **Error Handling / Exception Routing** | Missing PC master → `ERR-MAP-PC-004` → DLQ. |

---

## 7. Domain 6 — Material Ledger & Valuation

**Source Tables:** `CKMLCR`, `CKMLKEPH`, `MBEW`, `MARA`
**Target Entity:** `materialValuation`
**ODP Provider:** `0IC_C03`
**Mapping Count: 4 (MAP-ML-001 → MAP-ML-004)**

---

### MAP-ML-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-ML-001 |
| **Source Entity & Field** | `CKMLCR.MATNR` + `CKMLCR.BWKEY` |
| **Target Entity & Attribute** | `materialValuation.materialId` + `materialValuation.valuationArea` + `materialValuation.plantCode` |
| **Data Type (Source → Target)** | `CHAR(18)` + `CHAR(4)` → `String` + `String(4)` + `String(4)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `materialId = LTRIM(MATNR, '0')` — strip leading zeros (SAP stores material numbers zero-padded to 18 chars). `valuationArea = TRIM(BWKEY)`. In Meridian's configuration, valuation area = plant code (plant-level valuation). `plantCode = valuationArea`. Composite key: `CONCAT(LTRIM(MATNR,'0'), '-', BWKEY)`. |
| **Validation Rule** | `MATNR` must exist in `MARA`. `BWKEY` must be a valid plant in `T001W`. |
| **Error Handling / Exception Routing** | Material not in MARA → `ERR-MAP-ML-001` → DLQ. Unknown valuation area → `ERR-MAP-ML-001-VA` → DLQ. |

---

### MAP-ML-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-ML-002 |
| **Source Entity & Field** | `MBEW.STPRS` + `CKMLCR.PVPRS` + `MBEW.VPRSV` |
| **Target Entity & Attribute** | `materialValuation.standardPrice` + `materialValuation.periodicUnitPrice` + `materialValuation.priceControlIndicator` + `materialValuation.activePriceType` |
| **Data Type (Source → Target)** | `CURR(11,2)` + `CURR(11,2)` + `CHAR(1)` → `String` + `String` + `String(1)` + `String(1)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `standardPrice = MBEW.STPRS.toPlainString()` (SAP Standard Price). `periodicUnitPrice = CKMLCR.PVPRS.toPlainString()` (ML Periodic Moving Average). `priceControlIndicator = MBEW.VPRSV` (`S` = Standard Price, `V` = Moving Average Price). `activePriceType`: `IF VPRSV = 'S' THEN 'STANDARD'; ELSE 'MOVING_AVERAGE'; END`. With Material Ledger active, actual COGS uses `PVPRS` regardless of `VPRSV`. |
| **Validation Rule** | `STPRS ≥ 0`. `PVPRS ≥ 0`. `VPRSV IN ['S', 'V']`. |
| **Error Handling / Exception Routing** | Negative price → `ERR-MAP-ML-002` → Warning + alert to MM Costing team. |

---

### MAP-ML-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-ML-003 |
| **Source Entity & Field** | `CKMLCR.LBKUM` + `CKMLCR.SALK3` |
| **Target Entity & Attribute** | `materialValuation.totalStockQty` + `materialValuation.totalStockValue` + `materialValuation.movingAveragePrice` |
| **Data Type (Source → Target)** | `QUAN(13,3)` + `CURR(13,2)` → `BigDecimal` + `String` + `String` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `totalStockQty = LBKUM` (unrestricted stock quantity). `totalStockValue.amount = SALK3.toPlainString()` (total stock value in CC currency). Compute MAP: `IF LBKUM > 0 THEN movingAveragePrice = ROUND(SALK3 / LBKUM, 4).toPlainString(); ELSE movingAveragePrice = '0.0000'; END`. Currency = `MBEW.WAERS` (always INR for Meridian). |
| **Validation Rule** | `LBKUM ≥ 0`. `SALK3 ≥ 0`. If `LBKUM > 0`, `SALK3 > 0` (stock with zero value indicates costing issue). |
| **Error Handling / Exception Routing** | `LBKUM > 0 AND SALK3 = 0` → `ERR-MAP-ML-003-ZERO-VAL` → Warning + alert to Costing team. |

---

### MAP-ML-004

| Column | Value |
|---|---|
| **Mapping ID** | MAP-ML-004 |
| **Source Entity & Field** | `CKMLKEPH.KSTAR` + `CKMLKEPH.WKGBTR` + `CKMLKEPH.TYPPS` |
| **Target Entity & Attribute** | `materialValuation.priceVariance.costElement` + `.varianceAmount` + `.varianceCategory` |
| **Data Type (Source → Target)** | `CHAR(10)` + `CURR(13,2)` + `CHAR(1)` → `String` + `String` + `String(30)` |
| **Mandatory / Nullable** | Nullable (only when ML price differences exist) |
| **Transformation Rule & Business Logic** | `CKMLKEPH` = ML cost component split header. `costElement = TRIM(KSTAR)`. `varianceAmount.amount = WKGBTR.toPlainString()`. `TYPPS` = price variance type: `{B→'PRICE_DIFFERENCE', P→'EXCHANGE_RATE_DIFFERENCE', V→'TRANSFER_PRICE_REVALUATION', K→'COST_OF_GOODS_MANUFACTURED', G→'USAGE_VARIANCE'}`. Variance amounts are allocated back to production orders via ML settlement. |
| **Validation Rule** | `KSTAR` in CSKA. `TYPPS` in defined enum. |
| **Error Handling / Exception Routing** | Unknown variance type → `ERR-MAP-ML-004` → Warning, set `varianceCategory = 'OTHER'`. |

---

## 8. Domain 7 — Purchase Orders & Procurement

**Source Tables:** `EKKO`, `EKPO`, `EKET`, `EKKN`
**Target Entity:** `purchaseOrder`
**Mapping Count: 4 (MAP-PO-001 → MAP-PO-004)**

---

### MAP-PO-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-PO-001 |
| **Source Entity & Field** | `EKKO.EBELN` + `EKPO.EBELP` |
| **Target Entity & Attribute** | `purchaseOrder.poId` + `purchaseOrder.lineItem.lineItemId` |
| **Data Type (Source → Target)** | `CHAR(10)` + `NUMC(5)` → `String` + `String` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `poId = LTRIM(EBELN, '0')`. `lineItemId = LTRIM(EBELP, '0')`. Composite line key: `CONCAT(LTRIM(EBELN,'0'), '-', LTRIM(EBELP,'0'))` e.g. `"4500001234-10"`. Join `EKPO` on `(EBELN, EBELP)`. |
| **Validation Rule** | `EBELN` not null. `EBELP` not null. |
| **Error Handling / Exception Routing** | Missing EKPO line → `ERR-MAP-PO-001` → DLQ. |

---

### MAP-PO-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-PO-002 |
| **Source Entity & Field** | `EKPO.NETPR` + `EKPO.WAERS` + `EKPO.PEINH` + `EKPO.MEINS` |
| **Target Entity & Attribute** | `purchaseOrder.lineItem.netPricePerUnit` + `.orderUnit` + `.priceUnit` |
| **Data Type (Source → Target)** | `CURR(11,2)` + `CHAR(5)` + `QUAN(5,0)` + `UNIT(3)` → `String` + `String(3)` + `String(3)` + `Integer` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `netPricePerUnit.amount = NETPR.toPlainString()`. `netPricePerUnit.currency = TRIM(WAERS)`. `orderUnit = ISO_UOM_MAP[TRIM(MEINS)]` — translate SAP internal UoM to ISO UN/CEFACT unit codes: `{KG→'KGM', TO→'TNE', M→'MTR', L→'LTR', PC→'H87', EA→'C62', ST→'C62'}`. `priceUnit = INT(PEINH)` (e.g., 1 = per unit, 100 = per 100 units). |
| **Validation Rule** | `NETPR ≥ 0`. MEINS must be in ISO UoM translation table. `PEINH > 0`. |
| **Error Handling / Exception Routing** | Unknown UoM → `ERR-MAP-PO-002-UOM` → DLQ with UoM mapping alert. |

---

### MAP-PO-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-PO-003 |
| **Source Entity & Field** | `EKPO.MENGE` + `EKET.WEMNG` + `EKPO.NETWR` + `EKET.WEWRT` |
| **Target Entity & Attribute** | `purchaseOrder.lineItem.orderedQty` + `.goodsReceiptQty` + `.orderedValue` + `.goodsReceiptValue` + `.grIrOpenBalance` |
| **Data Type (Source → Target)** | `QUAN(13,3)` × 2 + `CURR(13,2)` × 2 → `BigDecimal` × 2 + `String` × 3 |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `orderedQty = EKPO.MENGE`. `goodsReceiptQty = SUM(EKET.WEMNG)` (sum across all delivery schedule lines). `orderedValue.amount = EKPO.NETWR.toPlainString()`. `goodsReceiptValue.amount = SUM(EKET.WEWRT).toPlainString()`. GR/IR open balance: `grIrOpenBalance.amount = (orderedValue - goodsReceiptValue).toPlainString()`. `grIrStatus`: `IF grIrOpenBalance = 0 THEN 'FULLY_RECEIVED'; ELSE IF goodsReceiptQty = 0 THEN 'NOT_RECEIVED'; ELSE 'PARTIALLY_RECEIVED'; END`. |
| **Validation Rule** | `orderedQty ≥ 0`. `goodsReceiptQty ≤ orderedQty * 1.1` (max 10% over-delivery). |
| **Error Handling / Exception Routing** | `goodsReceiptQty > orderedQty * 1.1` → `ERR-MAP-PO-003-OD` → Warning + alert to Procurement. |

---

### MAP-PO-004

| Column | Value |
|---|---|
| **Mapping ID** | MAP-PO-004 |
| **Source Entity & Field** | `EKKN.KOSTL` + `EKKN.PRCTR` + `EKKN.SAKTO` + `EKKN.AUFNR` |
| **Target Entity & Attribute** | `purchaseOrder.lineItem.accountAssignment.costCentreId` + `.profitCentreId` + `.glAccount` + `.internalOrderId` |
| **Data Type (Source → Target)** | `CHAR(10)` × 4 → `String` × 4 |
| **Mandatory / Nullable** | Nullable (only for account-assigned POs) |
| **Transformation Rule & Business Logic** | Join `EKKN` on `(EBELN, EBELP)`. `costCentreId = TRIM(KOSTL)`. `profitCentreId = TRIM(PRCTR)`. `glAccount = TRIM(SAKTO)`. `internalOrderId = LTRIM(AUFNR, '0')`. Multi-account-assignment: if multiple `EKKN` rows, create array of account assignments with percentage split (`EKKN.PCTEI`). |
| **Validation Rule** | At least one of `KOSTL` or `AUFNR` must be populated for non-stock PO lines. All referenced objects must exist in master. |
| **Error Handling / Exception Routing** | Missing account assignment for non-stock line → `ERR-MAP-PO-004` → Warning. |

---

## 9. Domain 8 — Sales Orders

**Source Tables:** `VBAK`, `VBAP`, `VBEP`
**Target Entity:** `salesOrder`
**Mapping Count: 3 (MAP-SO-001 → MAP-SO-003)**

---

### MAP-SO-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-SO-001 |
| **Source Entity & Field** | `VBAK.VBELN` + `VBAP.POSNR` |
| **Target Entity & Attribute** | `salesOrder.soId` + `salesOrder.lineItem.lineItemId` |
| **Data Type (Source → Target)** | `CHAR(10)` + `NUMC(6)` → `String` + `String` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `soId = LTRIM(VBELN, '0')`. `lineItemId = LTRIM(POSNR, '0')`. Composite: `CONCAT(LTRIM(VBELN,'0'), '-', LTRIM(POSNR,'0'))` e.g. `"10000001-10"`. Join `VBAP` on `(VBELN, POSNR)`. |
| **Validation Rule** | `VBELN` not null. `POSNR` not null. |
| **Error Handling / Exception Routing** | Missing VBAP → `ERR-MAP-SO-001` → DLQ. |

---

### MAP-SO-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-SO-002 |
| **Source Entity & Field** | `VBAP.NETWR` + `VBAP.WAERK` + `VBAP.FAKSP` |
| **Target Entity & Attribute** | `salesOrder.lineItem.netOrderValue` + `.orderCurrency` + `.billingBlock` + `.isBillingBlocked` |
| **Data Type (Source → Target)** | `CURR(13,2)` + `CHAR(5)` + `CHAR(2)` → `String` + `String(3)` + `String(2)` + `Boolean` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `netOrderValue.amount = NETWR.toPlainString()`. `orderCurrency = TRIM(WAERK)`. `billingBlock = TRIM(FAKSP)` (null if blank). `isBillingBlocked = (FAKSP IS NOT NULL AND FAKSP ≠ '')`. Lookup block description from `TVFST.VTEXT WHERE FAKSP = VBAP.FAKSP AND SPRAS = 'EN'`. |
| **Validation Rule** | `NETWR ≥ 0`. `WAERK` valid ISO 4217. |
| **Error Handling / Exception Routing** | Negative net value → `ERR-MAP-SO-002` → Warning (credit memos can have negative values; flag as `isCreditMemo = true`). |

---

### MAP-SO-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-SO-003 |
| **Source Entity & Field** | `VBEP.EDATU` + `VBAK.BSTDK` + `VBAP.ABGRU` |
| **Target Entity & Attribute** | `salesOrder.lineItem.confirmedDeliveryDate` + `salesOrder.customerRequestedDate` + `salesOrder.lineItem.rejectionReason` + `salesOrder.lineItem.isRejected` |
| **Data Type (Source → Target)** | `DATS` + `DATS` + `CHAR(2)` → `LocalDate` + `LocalDate` + `String(2)` + `Boolean` |
| **Mandatory / Nullable** | Nullable |
| **Transformation Rule & Business Logic** | `confirmedDeliveryDate = parse_DATS(MIN(VBEP.EDATU))` (earliest confirmed schedule line). `customerRequestedDate = parse_DATS(VBAK.BSTDK)`. `isRejected = (ABGRU IS NOT NULL AND ABGRU ≠ '')`. `rejectionReason`: lookup from `TVAG.BEZEI WHERE ABGRU = VBAP.ABGRU AND SPRAS = 'EN'`. Derive `deliveryDateVarianceDays = DATEDIFF(confirmedDeliveryDate, customerRequestedDate)`. |
| **Validation Rule** | Dates not `00000000` if non-null. |
| **Error Handling / Exception Routing** | Missing schedule line → `ERR-MAP-SO-003` → Warning, set `confirmedDeliveryDate = null`. |

---

## 10. Domain 9 — Fixed Assets

**Source Tables:** `ANLA`, `ANLC`, `ANLZ`, `ANEK`
**Target Entity:** `fixedAsset`
**ODP Provider:** `0FI_AA_11`
**Mapping Count: 2 (MAP-FA-001 → MAP-FA-002)**

---

### MAP-FA-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-FA-001 |
| **Source Entity & Field** | `ANLA.ANLN1` + `ANLA.ANLN2` + `ANLA.TXT50` + `ANLA.ANLKL` |
| **Target Entity & Attribute** | `fixedAsset.assetId` + `fixedAsset.assetDescription` + `fixedAsset.assetClass` |
| **Data Type (Source → Target)** | `CHAR(12)` + `CHAR(4)` + `CHAR(50)` + `CHAR(8)` → `String` + `String(50)` + `String(8)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `assetId = CONCAT(LTRIM(ANLN1,'0'), '-', LTRIM(ANLN2,'0'))` e.g. `"100000-0"`. Main number (`ANLN2 = '0000'`) = main asset; `ANLN2 > '0000'` = sub-asset. `assetDescription = TRIM(TXT50)`. `assetClass = TRIM(ANLKL)`. Lookup asset class description from `ANKT.TXT50 WHERE ANLKL = ANLA.ANLKL AND SPRAS = 'EN'`. |
| **Validation Rule** | `ANLN1` not null. `TXT50` not null. `ANLKL` must exist in `ANKA`. |
| **Error Handling / Exception Routing** | Asset class not in ANKA → `ERR-MAP-FA-001` → DLQ. |

---

### MAP-FA-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-FA-002 |
| **Source Entity & Field** | `ANLC.KANSW` + `ANLC.KNAFA` + `ANLC.NAFAB` + `ANLZ.AFASL` + `ANLZ.NDJAR` |
| **Target Entity & Attribute** | `fixedAsset.acquisitionValue` + `fixedAsset.accumulatedDepreciation` + `fixedAsset.netBookValue` + `fixedAsset.depreciationMethod` + `fixedAsset.usefulLifeYears` |
| **Data Type (Source → Target)** | `CURR(13,2)` × 3 + `CHAR(4)` + `NUMC(3)` → `String` × 3 + `String(30)` + `Integer` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `ANLC` = Asset Values (per depreciation area). Join on `(BUKRS, ANLN1, ANLN2, AFABE, GJAHR)` where `AFABE = '01'` (book depreciation). `acquisitionValue.amount = KANSW.toPlainString()`. `accumulatedDepreciation.amount = KNAFA.toPlainString()`. `netBookValue.amount = (KANSW - KNAFA).toPlainString()`. `plannedDepreciation.amount = NAFAB.toPlainString()`. `ANLZ.AFASL` = depreciation key: `{LINR→'STRAIGHT_LINE', GDBR→'WRITTEN_DOWN_VALUE', MANU→'MANUAL', DGNL→'DECLINING_BALANCE'}`. `usefulLifeYears = INT(NDJAR)`. |
| **Validation Rule** | `KANSW ≥ 0`. `KNAFA ≤ KANSW` (accumulated depreciation cannot exceed acquisition value). `NDJAR ∈ [1, 99]`. `AFASL` in defined enum. |
| **Error Handling / Exception Routing** | `KNAFA > KANSW` → `ERR-MAP-FA-002-OVER-DEP` → DLQ + Finance alert. Unknown depreciation key → `ERR-MAP-FA-002-DEP` → Warning, set `depreciationMethod = 'UNKNOWN'`. |

---

## 11. Domain 10 — Bank Statements & Cash

**Source Tables:** `FEBEP`, `FEBKO`, `T012K`
**Target Entity:** `bankStatement`
**Mapping Count: 3 (MAP-BK-001 → MAP-BK-003)**

---

### MAP-BK-001

| Column | Value |
|---|---|
| **Mapping ID** | MAP-BK-001 |
| **Source Entity & Field** | `FEBKO.HBKID` + `FEBKO.HKTID` + `T012K.BANKN` + `T012K.BANKL` |
| **Target Entity & Attribute** | `bankStatement.houseBank` + `bankStatement.accountId` + `bankStatement.bankAccountNumber` + `bankStatement.bankKey` |
| **Data Type (Source → Target)** | `CHAR(5)` + `CHAR(5)` + `CHAR(18)` + `CHAR(15)` → `String` × 4 |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `houseBank = TRIM(HBKID)`. `accountId = TRIM(HKTID)`. Join `T012K` on `(BUKRS, HBKID, HKTID)` for `BANKN` (account number) and `BANKL` (bank key / IFSC code in India). `bankAccountNumber = TRIM(BANKN)`. `bankKey = TRIM(BANKL)`. For Indian banks, `BANKL` = IFSC code (11 chars). Validate IFSC format. |
| **Validation Rule** | `HBKID` not null. `HKTID` not null. IFSC regex: `^[A-Z]{4}0[A-Z0-9]{6}$`. |
| **Error Handling / Exception Routing** | Invalid IFSC → `ERR-MAP-BK-001` → Warning, set `isIfscValid: false`. |

---

### MAP-BK-002

| Column | Value |
|---|---|
| **Mapping ID** | MAP-BK-002 |
| **Source Entity & Field** | `FEBEP.VALUT` + `FEBEP.BUDAT` + `FEBEP.WRBTR` + `FEBEP.WAERS` + `FEBEP.SGTXT` |
| **Target Entity & Attribute** | `bankStatement.lineItem.valueDate` + `.postingDate` + `.transactionAmount` + `.description` |
| **Data Type (Source → Target)** | `DATS` + `DATS` + `CURR(13,2)` + `CHAR(5)` + `CHAR(50)` → `LocalDate` + `LocalDate` + `String` + `String(3)` + `String(50)` |
| **Mandatory / Nullable** | **Mandatory** |
| **Transformation Rule & Business Logic** | `valueDate = parse_DATS(VALUT)` (value date = effective date for interest calculation). `postingDate = parse_DATS(BUDAT)`. `transactionAmount.amount = WRBTR.toPlainString()`. Signed: positive = debit (payment out), negative = credit (receipt). `transactionAmount.currency = TRIM(WAERS)`. `description = TRIM(SGTXT)`. |
| **Validation Rule** | `VALUT` not null. `WRBTR` not null. `valueDate ≤ postingDate + 5 days` (value date should not significantly post-date posting date). |
| **Error Handling / Exception Routing** | `valueDate > postingDate + 5` → `ERR-MAP-BK-002-VALDT` → Warning flag. |

---

### MAP-BK-003

| Column | Value |
|---|---|
| **Mapping ID** | MAP-BK-003 |
| **Source Entity & Field** | `FEBEP.XCLR` + `FEBEP.AUGBL` + `FEBEP.AUGDT` + `FEBKO.OPENO` + `FEBKO.CLOSO` |
| **Target Entity & Attribute** | `bankStatement.lineItem.isCleared` + `.clearingDocument` + `.clearingDate` + `bankStatement.openingBalance` + `bankStatement.closingBalance` |
| **Data Type (Source → Target)** | `CHAR(1)` + `NUMC(10)` + `DATS` + `CURR(13,2)` × 2 → `Boolean` + `String` + `LocalDate` + `String` × 2 |
| **Mandatory / Nullable** | `isCleared`: Mandatory; `clearingDocument`: Nullable; balances: Mandatory |
| **Transformation Rule & Business Logic** | `isCleared = (XCLR = 'X')`. `clearingDocument`: if cleared → `CONCAT(BUKRS, '-', GJAHR, '-', LTRIM(AUGBL,'0'))`. `clearingDate = parse_DATS(AUGDT)` if `XCLR = 'X'`. `openingBalance.amount = FEBKO.OPENO.toPlainString()`. `closingBalance.amount = FEBKO.CLOSO.toPlainString()`. Balance validation: `closingBalance = openingBalance + SUM(cleared line items)`. |
| **Validation Rule** | Balance equation check: `ABS(closingBalance - openingBalance - SUM(lineItems)) < 0.01 INR`. |
| **Error Handling / Exception Routing** | Balance mismatch > INR 0.01 → `ERR-MAP-BK-003-BAL` → DLQ + Treasury alert. |

---

## 12. Algorithm A — Recursive Hierarchy Flattening

### Overview

SAP stores cost centre and profit centre hierarchies in two tables:
- `SETNODE` — internal hierarchy nodes (groups containing other groups or leaves)
- `SETLEAF` — hierarchy leaves (actual cost centre values assigned to groups)

The hierarchy can be up to **7 levels deep** in Meridian's configuration. FinSight requires a **flat, denormalized representation** (L1–L7 dimension keys) for OLAP query performance. This algorithm traverses the hierarchy bottom-up from leaf to root and populates all levels.

---

### Pseudo-Code

```
FUNCTION flattenCostCentreHierarchy(kostl: String, setId: String, kokrs: String) -> HierarchyPath

  /**
   * INPUTS:
   *   kostl  : Cost Centre code (leaf node value, e.g., "CC_MH_PROD_01")
   *   setId  : Root hierarchy set ID (e.g., "MERI_CC_H1")
   *   kokrs  : Controlling area (e.g., "MFGL")
   *
   * OUTPUT:
   *   HierarchyPath { L1, L2, L3, L4, L5, L6, L7, fullPath }
   */

  // Step 1: Find leaf node entry in SETLEAF
  leafRecord = SELECT * FROM SETLEAF
               WHERE SETNAME = setId
                 AND KOKRS   = kokrs
                 AND FROM_VAL <= kostl
                 AND TO_VAL   >= kostl
                 AND SUBSETTYPE = 'K'   -- 'K' = Cost Centre type

  IF leafRecord IS NULL THEN
    THROW HierarchyException("Cost centre " + kostl + " not found in set " + setId)
  END

  // Step 2: Initialise ancestor stack
  ancestors = EMPTY_STACK           // will hold [immediate_parent, ..., root]
  currentSetName = leafRecord.SETNAME

  // Step 3: Traverse upward through SETNODE
  WHILE currentSetName IS NOT NULL DO
    nodeRecord = SELECT * FROM SETNODE
                 WHERE SUBSETNAME = currentSetName
                   AND KOKRS      = kokrs

    IF nodeRecord IS NULL THEN
      BREAK   // reached root (no parent node)
    END

    // Push the parent set onto the ancestor stack
    ancestors.PUSH(nodeRecord.SETNAME)
    currentSetName = nodeRecord.SETNAME
  END

  // Step 4: Reverse stack to get root-to-leaf order
  pathNodes = REVERSE(ancestors)    // [L1_root, L2, L3, ..., Ln_parent_of_leaf]
  pathNodes.APPEND(kostl)           // append the leaf (cost centre itself)

  // Step 5: Map nodes to L1–L7 dimensions (pad with nulls if < 7 levels)
  levels = ARRAY[7] filled with NULL

  FOR i = 0 TO MIN(LEN(pathNodes) - 1, 6) DO
    levels[i] = pathNodes[i]
  END

  // Step 6: Build result
  hierarchyPath = HierarchyPath {
    L1       : levels[0],          // Root hierarchy group
    L2       : levels[1],
    L3       : levels[2],
    L4       : levels[3],
    L5       : levels[4],
    L6       : levels[5],
    L7       : levels[6],          // Leaf (actual cost centre)
    fullPath : JOIN(pathNodes, '/')
  }

  RETURN hierarchyPath

END FUNCTION
```

---

### SQL Implementation (PostgreSQL / TimescaleDB — Reference Data Store)

The hierarchy reference data is replicated nightly from SAP into PostgreSQL for fast in-process lookups (eliminating live RFC calls per record):

```sql
-- Recursive CTE for hierarchy flattening
-- Executed once per cost centre during the nightly hierarchy refresh job
-- Results cached in Redis for 24h per cost centre

WITH RECURSIVE cc_hierarchy AS (

    -- Anchor: start from the leaf (the actual cost centre)
    SELECT
        sl.FROM_VAL                     AS cost_centre,
        sl.SETNAME                      AS parent_set,
        sl.FROM_VAL                     AS node_name,
        1                               AS level,
        ARRAY[sl.FROM_VAL]              AS path_array
    FROM sap_setleaf sl
    WHERE sl.SETNAME   = 'MERI_CC_H1'
      AND sl.KOKRS     = 'MFGL'
      AND sl.FROM_VAL  = :kostl       -- parameterised by cost centre

    UNION ALL

    -- Recursive step: walk up to parent nodes
    SELECT
        ch.cost_centre,
        sn.SETNAME                      AS parent_set,
        sn.SETNAME                      AS node_name,
        ch.level + 1,
        ARRAY_PREPEND(sn.SETNAME, ch.path_array)
    FROM sap_setnode sn
    INNER JOIN cc_hierarchy ch ON sn.SUBSETNAME = ch.parent_set
    WHERE ch.level < 8              -- safety guard: max 7 levels + 1 overflow check

)

-- Select the deepest traversal result (max level = root reached)
SELECT
    cost_centre,
    path_array,
    COALESCE(path_array[1], NULL)   AS hierarchy_l1,
    COALESCE(path_array[2], NULL)   AS hierarchy_l2,
    COALESCE(path_array[3], NULL)   AS hierarchy_l3,
    COALESCE(path_array[4], NULL)   AS hierarchy_l4,
    COALESCE(path_array[5], NULL)   AS hierarchy_l5,
    COALESCE(path_array[6], NULL)   AS hierarchy_l6,
    COALESCE(path_array[7], NULL)   AS hierarchy_l7,
    ARRAY_TO_STRING(path_array, '/') AS full_path
FROM cc_hierarchy
ORDER BY level DESC
LIMIT 1;
```

---

### Hierarchy Cache Strategy

```
On Transformation Worker startup:
  1. Load ALL active cost centres from CSKS (DATAB ≤ TODAY ≤ DATBI)
  2. For each cost centre, execute hierarchy CTE above
  3. Store result in Redis hash:
       Key  : "cc:hier:{kokrs}:{kostl}"
       Value: JSON { L1, L2, L3, L4, L5, L6, L7, fullPath }
       TTL  : 86400 seconds (24 hours)

On each transformation:
  1. Redis GET "cc:hier:MFGL:{kostl}"
  2. IF hit → return cached HierarchyPath
  3. IF miss → execute SQL CTE → cache result → return HierarchyPath
  4. IF SQL fails → ERR-MAP-GL-011-HIER → set hierarchyPath = null, continue

Nightly refresh (05:00 IST, post batch-blackout):
  1. Full reload of SETNODE, SETLEAF from SAP via RFC_READ_TABLE
  2. Rebuild all hierarchy paths
  3. Atomic Redis mass-SET (pipeline mode) with 24h TTL
  4. Log refresh count and duration to PostgreSQL pipeline_runs table
```

---

## 13. Algorithm B — TCURR Triangulation & Point-in-Time Rate Lookup

### Overview

Meridian posts transactions in INR (primary), USD, EUR, GBP, and JPY. When `ACDOCA.WAERS ≠ ACDOCA.HWAER` (transaction currency ≠ company code currency), the Transformation Worker must resolve the exchange rate used by SAP at posting time from the `TCURR` table. FinSight requires the **exact rate used by SAP** (not a live market rate) to ensure reconciliation fidelity.

---

### SAP TCURR Table Structure

```
TCURR: Exchange Rate Table
  MANDT : Client
  KURST : Exchange Rate Type (e.g., 'M' = Average, 'B' = Bank Selling, 'G' = Bank Buying)
  FCURR : From Currency (foreign currency)
  TCURR : To Currency (company code currency)
  GDATU : Valid-from date (stored as inverted date: 99999999 - YYYYMMDD)
  UKURS : Exchange Rate (direct quotation: how many TCURR units per 1 FCURR)
  FFACT : From currency factor
  TFACT : To currency factor

Note: GDATU is stored inverted. Actual valid-from date = 99999999 - GDATU
```

---

### Pseudo-Code

```
FUNCTION resolveExchangeRate(
    fcurr    : String,    -- From currency (transaction currency)
    tcurr    : String,    -- To currency (company code currency, always 'INR')
    kurst    : String,    -- Exchange rate type (default 'M' for Meridian)
    budat    : LocalDate  -- Posting date (point-in-time lookup)
) -> ExchangeRate

  /**
   * SAP TCURR stores the MOST RECENT rate valid on or before BUDAT.
   * Rates are effective from their GDATU date until superseded by a newer rate.
   * Triangulation is needed when direct FCurr→TCurr rate does not exist.
   */

  // Step 1: Direct lookup — FCurr → INR
  invertedDate = 99999999 - DATE_TO_INT(budat)    -- SAP inverted date

  directRate = SELECT UKURS, FFACT, TFACT
               FROM TCURR
               WHERE KURST = kurst
                 AND FCURR = fcurr
                 AND TCURR = 'INR'
                 AND GDATU >= invertedDate          -- most recent rate on/before budat
               ORDER BY GDATU ASC                  -- ASC on inverted date = newest first
               LIMIT 1

  IF directRate IS NOT NULL THEN
    RETURN ExchangeRate {
      rate    : (directRate.UKURS * directRate.TFACT) / directRate.FFACT,
      method  : 'DIRECT',
      source  : 'TCURR',
      rateDate: budat
    }
  END

  // Step 2: Triangulation via USD (most liquid intermediate currency)
  rateToUSD = SELECT UKURS, FFACT, TFACT FROM TCURR
              WHERE KURST = kurst AND FCURR = fcurr AND TCURR = 'USD'
              AND GDATU >= invertedDate ORDER BY GDATU ASC LIMIT 1

  rateUSDtoINR = SELECT UKURS, FFACT, TFACT FROM TCURR
                 WHERE KURST = kurst AND FCURR = 'USD' AND TCURR = 'INR'
                 AND GDATU >= invertedDate ORDER BY GDATU ASC LIMIT 1

  IF rateToUSD IS NOT NULL AND rateUSDtoINR IS NOT NULL THEN
    fcurrInUSD  = (rateToUSD.UKURS * rateToUSD.TFACT) / rateToUSD.FFACT
    usdInINR    = (rateUSDtoINR.UKURS * rateUSDtoINR.TFACT) / rateUSDtoINR.FFACT
    triangulatedRate = fcurrInUSD * usdInINR
    RETURN ExchangeRate {
      rate    : triangulatedRate,
      method  : 'TRIANGULATED_VIA_USD',
      source  : 'TCURR',
      rateDate: budat
    }
  END

  // Step 3: Fallback 1 — Use rate from previous business day (T-1)
  prevDate = PREVIOUS_BUSINESS_DAY(budat)
  invertedPrevDate = 99999999 - DATE_TO_INT(prevDate)

  fallbackRate = SELECT UKURS, FFACT, TFACT FROM TCURR
                 WHERE KURST = kurst AND FCURR = fcurr AND TCURR = 'INR'
                 AND GDATU >= invertedPrevDate ORDER BY GDATU ASC LIMIT 1

  IF fallbackRate IS NOT NULL THEN
    LOG WARNING "FX-FALLBACK-T1: No rate for {fcurr}/INR on {budat}. Using T-1 rate from {prevDate}."
    RETURN ExchangeRate {
      rate     : (fallbackRate.UKURS * fallbackRate.TFACT) / fallbackRate.FFACT,
      method   : 'FALLBACK_T1',
      source   : 'TCURR',
      rateDate : prevDate,
      isFallback: true,
      fallbackReason: "No rate on posting date; T-1 rate applied"
    }
  END

  // Step 4: Fallback 2 — Use most recent available rate (within 7 days)
  FOR dayOffset = 2 TO 7 DO
    tryDate = budat - dayOffset days
    invertedTryDate = 99999999 - DATE_TO_INT(tryDate)
    bestRate = SELECT ... WHERE GDATU >= invertedTryDate ORDER BY GDATU ASC LIMIT 1
    IF bestRate IS NOT NULL THEN
      LOG WARNING "FX-FALLBACK-T{dayOffset}: Rate found on {tryDate} ({dayOffset} days before posting)."
      RETURN ExchangeRate { rate: ..., method: "FALLBACK_T{dayOffset}", isFallback: true, ... }
    END
  END

  // Step 5: Fatal — No rate found within 7-day window
  LOG ERROR "FX-FATAL: No exchange rate found for {fcurr}/INR within 7 days of {budat}."
  THROW ExchangeRateNotFoundException(fcurr, 'INR', budat)
  -- Routes to ERR-MAP-GL-005-FX → DLQ

END FUNCTION
```

---

### Rate Application Formula

```
Given:
  WSL   = Transaction currency amount (ACDOCA.WSL)
  FCURR = Transaction currency (ACDOCA.WAERS)
  RATE  = resolveExchangeRate(FCURR, 'INR', 'M', BUDAT).rate

Compute Company Code Currency amount:
  HSL_computed = ROUND(WSL * RATE, 2)

Validate against SAP-stored HSL:
  IF ABS(HSL_computed - ACDOCA.HSL) > 0.05 THEN
    LOG WARNING "FX-VARIANCE: Computed HSL {HSL_computed} differs from SAP HSL {ACDOCA.HSL}
                 by {ABS(HSL_computed - HSL)}. Using SAP value (HSL) as authoritative."
  END

  -- ALWAYS use ACDOCA.HSL as the authoritative amount (SAP is source of truth).
  -- Rate computation is for audit metadata only.
```

---

### Redis Cache for FX Rates

```
Key    : "fx:{kurst}:{fcurr}:INR:{YYYYMMDD}"
Value  : JSON { rate, method, rateDate, isFallback }
TTL    : 86400 seconds (rates don't change intraday for a given date)

On startup:
  Pre-load last 30 days of TCURR rates for all Meridian currencies
  (USD, EUR, GBP, JPY, SGD, AED) into Redis for zero-latency lookups.
```

---

## 14. Algorithm C — Indian GST Split Preservation Logic

### Overview

Under the Indian Goods and Services Tax framework, each taxable supply carries a tri-component tax:
- **CGST** — Central GST (owed to Union Government)
- **SGST** — State GST (owed to State Government)  
- **IGST** — Integrated GST (for inter-state supplies; replaces CGST + SGST)

**Key rules:**
1. Intra-state supply: `CGST = SGST = (GST Rate / 2)`; `IGST = 0`
2. Inter-state supply: `IGST = GST Rate`; `CGST = SGST = 0`
3. Validation: `CGST + SGST + IGST = Total GST Amount`
4. All tax amounts must be in INR (regulatory requirement)

---

### SAP GST Storage

In SAP S/4HANA for India, GST amounts are stored in `BSET` (Tax Line Items) with condition type codes:

```
Condition Types (J_1IG* schema):
  JCST / JA1X : CGST tax condition type
  JAST / JA1Y : SGST tax condition type
  JISG / JA1Z : IGST tax condition type
  JCES        : Cess condition type

BSET Fields:
  BSET.KSCHL  : Condition type (JCST, JAST, JISG, JCES)
  BSET.HWBAS  : Tax base amount (INR)
  BSET.HWSTE  : Tax amount (INR)
  BSET.MWSKZ  : Tax code (e.g., I8, I5, I12)
```

---

### Pseudo-Code

```
FUNCTION extractAndValidateGSTSplit(
    bukrs : String,       -- Company code
    belnr : String,       -- Document number
    gjahr : String,       -- Fiscal year
    buzei : String        -- Line item number
) -> TaxSplit

  // Step 1: Fetch all tax lines for this document/line item
  taxLines = SELECT KSCHL, HWBAS, HWSTE, MWSKZ
             FROM BSET
             WHERE BUKRS = bukrs
               AND BELNR = belnr
               AND GJAHR = gjahr
               AND BUZEI = buzei

  // Step 2: Extract component amounts
  cgstAmount = 0.00
  sgstAmount = 0.00
  igstAmount = 0.00
  cessAmount = 0.00
  taxBaseAmount = 0.00

  FOR EACH taxLine IN taxLines DO
    CASE taxLine.KSCHL
      WHEN 'JCST', 'JA1X' THEN
        cgstAmount    = cgstAmount + taxLine.HWSTE
        taxBaseAmount = taxLine.HWBAS           -- base is same for all components

      WHEN 'JAST', 'JA1Y' THEN
        sgstAmount    = sgstAmount + taxLine.HWSTE

      WHEN 'JISG', 'JA1Z' THEN
        igstAmount    = igstAmount + taxLine.HWSTE

      WHEN 'JCES' THEN
        cessAmount    = cessAmount + taxLine.HWSTE

      ELSE
        LOG DEBUG "Unknown GST condition type: " + taxLine.KSCHL
    END CASE
  END FOR

  totalGstAmount = cgstAmount + sgstAmount + igstAmount + cessAmount

  // Step 3: Determine supply type
  supplyType = DERIVE_SUPPLY_TYPE(bukrs, belnr)
  /*
    DERIVE_SUPPLY_TYPE checks:
    - Vendor/customer state (LFA1.REGIO or KNA1.REGIO) vs company code state (T001.LAND1 + REGIO)
    - If same state → INTRA_STATE (CGST + SGST)
    - If different state → INTER_STATE (IGST only)
    - If export → EXPORT (zero-rated, IGST = 0 with LUT)
  */

  // Step 4: Validate GST split consistency
  tolerance = 0.02   -- INR 0.02 rounding tolerance

  IF supplyType = 'INTRA_STATE' THEN
    IF igstAmount > tolerance THEN
      RAISE GSTValidationError("INTRA_STATE supply has non-zero IGST: " + igstAmount)
      -- Route to ERR-MAP-GST-001
    END
    IF ABS(cgstAmount - sgstAmount) > tolerance THEN
      RAISE GSTValidationError("CGST (" + cgstAmount + ") ≠ SGST (" + sgstAmount + ")")
      -- Route to ERR-MAP-GST-002
    END

  ELSE IF supplyType = 'INTER_STATE' THEN
    IF cgstAmount > tolerance OR sgstAmount > tolerance THEN
      RAISE GSTValidationError("INTER_STATE supply has CGST/SGST: " + cgstAmount + "/" + sgstAmount)
      -- Route to ERR-MAP-GST-003
    END
  END

  // Step 5: Cross-check total against BSET HWSTE sum
  bsetTotal = SUM(taxLine.HWSTE FOR ALL taxLines)
  IF ABS(totalGstAmount - bsetTotal) > tolerance THEN
    RAISE GSTValidationError("GST component sum (" + totalGstAmount + ") ≠ BSET total (" + bsetTotal + ")")
    -- Route to ERR-MAP-GST-004
  END

  // Step 6: Build validated TaxSplit object
  taxSplit = TaxSplit {
    cgstAmount  : ROUND(cgstAmount, 2).toPlainString(),
    sgstAmount  : ROUND(sgstAmount, 2).toPlainString(),
    igstAmount  : ROUND(igstAmount, 2).toPlainString(),
    cessAmount  : ROUND(cessAmount, 2).toPlainString(),
    taxBaseAmount: ROUND(taxBaseAmount, 2).toPlainString(),
    totalGstAmount: ROUND(totalGstAmount, 2).toPlainString(),
    taxCurrency : 'INR',
    supplyType  : supplyType,
    isValid     : true
  }

  RETURN taxSplit

END FUNCTION
```

---

### GST Validation Matrix

| Validation ID | Rule | Supply Type | Tolerance | Error Code | Routing |
|---|---|---|---|---|---|
| GST-V01 | `CGST = SGST` | INTRA_STATE | INR 0.02 | `ERR-MAP-GST-002` | DLQ + Tax alert |
| GST-V02 | `IGST = 0` | INTRA_STATE | INR 0.02 | `ERR-MAP-GST-001` | DLQ + Tax alert |
| GST-V03 | `CGST = 0 AND SGST = 0` | INTER_STATE | INR 0.02 | `ERR-MAP-GST-003` | DLQ + Tax alert |
| GST-V04 | `CGST + SGST + IGST + CESS = BSET_TOTAL` | Any | INR 0.02 | `ERR-MAP-GST-004` | DLQ |
| GST-V05 | All amounts ≥ 0 | Any | — | `ERR-MAP-GST-005` | DLQ |
| GST-V06 | `taxCurrency = 'INR'` | Any | — | `ERR-MAP-GST-006` | DLQ (hard block) |
| GST-V07 | `taxBaseAmount > 0` if any tax component > 0 | Any | INR 0.01 | `ERR-MAP-GST-007` | Warning |
| GST-V08 | GSTIN state prefix matches supply type | INTRA_STATE | — | `ERR-MAP-GST-008` | Warning + ITC flag |

---

## 15. Error Code Registry

| Error Code | Domain | Severity | Description | Routing |
|---|---|---|---|---|
| `ERR-MAP-GL-001` | GL | CRITICAL | documentId construction failed (null component) | DLQ |
| `ERR-MAP-GL-002` | GL | CRITICAL | Invalid posting date (null or zero date) | DLQ |
| `ERR-MAP-GL-003` | GL | CRITICAL | Invalid fiscal period out of range [001-016] | DLQ |
| `ERR-MAP-GL-004` | GL | CRITICAL | Null company code currency amount | DLQ |
| `ERR-MAP-GL-004-CCY` | GL | CRITICAL | Non-INR company code currency detected | DLQ |
| `ERR-MAP-GL-005-FX` | GL | CRITICAL | Missing TCURR exchange rate (7-day window exhausted) | DLQ |
| `ERR-MAP-GL-006` | GL | CRITICAL | GL account not in Meridian CoA | DLQ |
| `ERR-MAP-GL-006-COA` | GL | HIGH | Missing Schedule III mapping for account | DLQ + Finance alert |
| `ERR-MAP-GL-007` | GL | CRITICAL | Invalid DRCRK value (not S or H) | DLQ |
| `ERR-MAP-GL-008` | GL | CRITICAL | Null document type (BLART) | DLQ |
| `ERR-MAP-GL-009` | GL | MEDIUM | BKPF header not found for reversal | Warning log |
| `ERR-MAP-GL-010` | GL | LOW | Profit centre not in CEPC master | Warning |
| `ERR-MAP-GL-011` | GL | LOW | Cost centre not in CSKS master | Warning |
| `ERR-MAP-GL-011-HIER` | GL | LOW | Hierarchy path resolution failure | Warning |
| `ERR-MAP-GL-012` | GL | HIGH | Self-intercompany reference (RASSC = BUKRS) | DLQ |
| `ERR-MAP-AP-001` | AP | CRITICAL | Vendor not in LFA1 master | DLQ |
| `ERR-MAP-AP-002` | AP | HIGH | Invalid GSTIN format | Warning + ITC flag |
| `ERR-MAP-AP-003` | AP | CRITICAL | Null baseline date (ZFBDT) | DLQ |
| `ERR-MAP-AP-003-DATE` | AP | CRITICAL | Net due date before baseline date | DLQ |
| `ERR-MAP-AP-004-NEG` | AP | LOW | Negative DMBTR on AP item | Warning |
| `ERR-MAP-AP-006` | AP | CRITICAL | TDS sum mismatch | DLQ + Tax alert |
| `ERR-MAP-AP-006-MISS` | AP | HIGH | Missing TDS for mandatory-TDS vendor | DLQ + Tax alert |
| `ERR-MAP-AP-007-206AA` | AP | HIGH | Missing PAN — Section 206AA 20% TDS | Alert to Tax team |
| `ERR-MAP-AP-008-DATE` | AP | HIGH | Clearing date before posting date | DLQ |
| `ERR-MAP-AR-002-OVR` | AR | HIGH | Credit utilisation > 120% | Warning + Credit Control alert |
| `ERR-MAP-FA-002-OVER-DEP` | FA | HIGH | Accumulated depreciation > acquisition value | DLQ + Finance alert |
| `ERR-MAP-BK-003-BAL` | BK | CRITICAL | Bank statement balance equation mismatch | DLQ + Treasury alert |
| `ERR-MAP-GST-001` | GST | CRITICAL | IGST non-zero on intra-state supply | DLQ + Tax alert |
| `ERR-MAP-GST-002` | GST | CRITICAL | CGST ≠ SGST on intra-state supply | DLQ + Tax alert |
| `ERR-MAP-GST-003` | GST | CRITICAL | CGST/SGST non-zero on inter-state supply | DLQ + Tax alert |
| `ERR-MAP-GST-004` | GST | CRITICAL | GST component sum ≠ BSET total | DLQ |
| `ERR-MAP-GST-006` | GST | CRITICAL | Tax amount not in INR (RBI/GST violation) | DLQ (hard block) |

---

## 16. Mapping Summary Matrix

| Domain | Range | Count | Source Tables | Target Entity |
|---|---|---|---|---|
| General Ledger | MAP-GL-001 → MAP-GL-012 | **12** | ACDOCA, BKPF | journalEntry |
| Accounts Payable | MAP-AP-001 → MAP-AP-008 | **8** | BSIK, BSAK, LFA1, LFC1, WITH_ITEM | apItem |
| Accounts Receivable | MAP-AR-001 → MAP-AR-008 | **8** | BSID, BSAD, KNA1, KNB1, KNKK | arItem |
| Cost Centre Accounting | MAP-CO-001 → MAP-CO-006 | **6** | CSKS, CSKT, ACDOCA | costCentre |
| Profit Centre Accounting | MAP-PC-001 → MAP-PC-004 | **4** | CEPC, CEPCT, ACDOCP | profitCentre |
| Material Ledger & Valuation | MAP-ML-001 → MAP-ML-004 | **4** | CKMLCR, CKMLKEPH, MBEW, MARA | materialValuation |
| Purchase Orders | MAP-PO-001 → MAP-PO-004 | **4** | EKKO, EKPO, EKET, EKKN | purchaseOrder |
| Sales Orders | MAP-SO-001 → MAP-SO-003 | **3** | VBAK, VBAP, VBEP | salesOrder |
| Fixed Assets | MAP-FA-001 → MAP-FA-002 | **2** | ANLA, ANLC, ANLZ, ANEK | fixedAsset |
| Bank Statements | MAP-BK-001 → MAP-BK-003 | **3** | FEBEP, FEBKO, T012K | bankStatement |
| **TOTAL** | | **54** | | |

---

### Appendix A: Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 24 Sep 2026 | Zetheta FDE-9B | Initial 30 mappings draft |
| 0.5 | 01 Oct 2026 | Zetheta FDE-9B | Expanded to 54 mappings; added GST algorithm |
| 1.0 | 04 Oct 2026 | Zetheta FDE-9B | Production-ready draft |

---

*Document Classification: CONFIDENTIAL – CLIENT RESTRICTED*
*© 2026 Zetheta Algorithms Pvt. Ltd. All rights reserved.*
*Reference: ZA-FDE-D3-MERIDIAN-001 v1.0.0 | 04 October 2026*
