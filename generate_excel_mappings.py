import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

base_dir = r"c:\Users\USER\OneDrive\Desktop\Custom_API_Integration\FDE-9B-[YourName]-Batch01"
mappings_dir = os.path.join(base_dir, "mappings")
os.makedirs(mappings_dir, exist_ok=True)
excel_path = os.path.join(mappings_dir, "MAP_Domains_01_10_Master.xlsx")

wb = openpyxl.Workbook()
# Setup summary sheet
ws_summary = wb.active
ws_summary.title = "Executive Summary"
ws_summary.views.sheetView[0].showGridLines = True

# Colors
navy_header = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
slate_sub = PatternFill(start_color="4A777A", end_color="4A777A", fill_type="solid")
accent_blue = PatternFill(start_color="E8F1F5", end_color="E8F1F5", fill_type="solid")
white_bold = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=16, bold=True, color="1B365D")
sub_font = Font(name="Calibri", size=11, italic=True, color="555555")
regular_font = Font(name="Calibri", size=10)
bold_font = Font(name="Calibri", size=10, bold=True)

thin_border = Border(
    left=Side(style='thin', color='D3D3D3'),
    right=Side(style='thin', color='D3D3D3'),
    top=Side(style='thin', color='D3D3D3'),
    bottom=Side(style='thin', color='D3D3D3')
)

# Executive Summary Content
ws_summary["A2"] = "MERIDIAN MANUFACTURING LTD. - SAP S/4HANA TO FINSIGHT 4.2"
ws_summary["A2"].font = title_font
ws_summary["A3"] = "Deliverable D3: Master Data Transformation and Field Mapping Workbook (54 Mappings across 10 Domains)"
ws_summary["A3"].font = sub_font

headers_summary = ["Domain ID", "Domain Name", "Primary SAP Tables", "Target FinSight Entity", "Mapping Count", "Key Transformation Logic"]
for col_idx, h in enumerate(headers_summary, start=1):
    cell = ws_summary.cell(row=5, column=col_idx, value=h)
    cell.fill = navy_header
    cell.font = white_bold
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

domains_summary = [
    ("DOM-01", "General Ledger Accounting", "ACDOCA, BKPF", "GL_TRANSACTIONS", 6, "Dual-entry balancing, V3 fiscal period derivation, Schedule III mapping"),
    ("DOM-02", "Accounts Payable & Vendor Master", "BSEG, BSIK, BSAK, LFA1, LFC1", "AP_OPEN_ITEMS, VENDOR_DIM", 6, "Payment terms calculation, AP aging tranches, MSME classification"),
    ("DOM-03", "Accounts Receivable & Customers", "BSID, BSAD, KNA1", "AR_OPEN_ITEMS, CUSTOMER_DIM", 5, "DSO calculation, credit limit utilization, GSTIN reconciliation"),
    ("DOM-04", "Cost Center Accounting & CO", "CSKS, CSKT, SETNODE, SETLEAF", "COST_CENTER_DIM, CO_ACTUALS", 6, "7-level hierarchy flattening, activity-type allocation, variance check"),
    ("DOM-05", "Profit Center Accounting", "CEPC, CEPCT", "PROFIT_CENTER_DIM", 5, "Segment reporting, inter-company profit elimination"),
    ("DOM-06", "Procurement & Materials (MM)", "EKKO, EKPO, MSEG", "PURCHASE_ORDERS, GR_IR_MATCH", 6, "P2P 3-way matching (PO-GR-IR), HSN code validation, price variance"),
    ("DOM-07", "Sales & Distribution (SD)", "VBAK, VBAP", "SALES_ORDERS, REVENUE_FACT", 5, "Order-to-Cash tracing, GST state tax split (CGST+SGST/IGST)"),
    ("DOM-08", "Fixed Asset Accounting (AA)", "ANLA, ANLP", "FIXED_ASSETS_DIM, DEPRECIATION_FACT", 5, "Useful life depreciation calculation, capitalization date check"),
    ("DOM-09", "Cash Management & Treasury", "FEBKO, FEBEP", "BANK_STATEMENTS, CASH_POSITION", 5, "MT940/CAMT.053 parsing, UTR reference matching, unallocated float"),
    ("DOM-10", "Currency Exchange & Rates", "TCURR", "EXCHANGE_RATES_DIM", 5, "Indirect quote inversion, mid-market rate extraction, triangulation")
]

for row_idx, data in enumerate(domains_summary, start=6):
    for col_idx, val in enumerate(data, start=1):
        cell = ws_summary.cell(row=row_idx, column=col_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        if col_idx in (1, 5):
            cell.alignment = Alignment(horizontal="center")

total_row = len(domains_summary) + 6
ws_summary.cell(row=total_row, column=1, value="TOTAL")
ws_summary.cell(row=total_row, column=1).font = bold_font
ws_summary.cell(row=total_row, column=5, value="=SUM(E6:E15)")
ws_summary.cell(row=total_row, column=5).font = bold_font
ws_summary.cell(row=total_row, column=5).alignment = Alignment(horizontal="center")

for col in range(1, 7):
    ws_summary.column_dimensions[get_column_letter(col)].width = 24
ws_summary.column_dimensions["B"].width = 32
ws_summary.column_dimensions["F"].width = 50

# Setup 54 Mappings Master Sheet
ws_master = wb.create_sheet(title="All 54 Field Mappings")
ws_master.views.sheetView[0].showGridLines = True

headers_master = [
    "Mapping ID", "Domain", "Source Entity & Field", "SAP Description", "Target Entity & Field",
    "Target Data Type", "Transformation Rule & Logic", "Nullability / Rules"
]

for col_idx, h in enumerate(headers_master, start=1):
    cell = ws_master.cell(row=1, column=col_idx, value=h)
    cell.fill = navy_header
    cell.font = white_bold
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Generate 54 concrete mappings
mappings_54 = [
    # DOM-01: GL
    ("MAP-GL-001", "GL Accounting", "ACDOCA.BELNR", "Accounting Document Number", "GL_TRANSACTIONS.document_number", "VARCHAR(10)", "Direct 1:1 alphanumeric transfer with leading zero preservation", "NOT NULL; DQ-001"),
    ("MAP-GL-002", "GL Accounting", "ACDOCA.DOCLN", "Line Item Number", "GL_TRANSACTIONS.line_item_id", "INTEGER", "Cast CHAR(6) to Integer; composite PK with BELNR", "NOT NULL; PK"),
    ("MAP-GL-003", "GL Accounting", "ACDOCA.BUDAT", "Posting Date in Document", "GL_TRANSACTIONS.posting_date", "DATE", "Convert YYYYMMDD to ISO-8601 YYYY-MM-DD", "NOT NULL; DQ-003"),
    ("MAP-GL-004", "GL Accounting", "ACDOCA.RACCT", "General Ledger Account Number", "GL_TRANSACTIONS.gl_account_code", "VARCHAR(10)", "Trim leading zeros; lookup Schedule III mapping node", "NOT NULL; DQ-004"),
    ("MAP-GL-005", "GL Accounting", "ACDOCA.HSL", "Amount in Local Currency (INR)", "GL_TRANSACTIONS.amount_local_inr", "DECIMAL(18,2)", "Preserve Decimal(18,2); sign determined by SHKZG ('S'=+, 'H'=-)", "NOT NULL; DQ-009"),
    ("MAP-GL-006", "GL Accounting", "ACDOCA.WERKS", "Plant Code", "GL_TRANSACTIONS.plant_id", "VARCHAR(4)", "Validate against Meridian 7 plant codes ('1100'..'1700')", "NOT NULL; DQ-002"),
    
    # DOM-02: AP
    ("MAP-AP-001", "Accounts Payable", "BSEG.LIFNR", "Vendor Account Number", "AP_OPEN_ITEMS.vendor_id", "VARCHAR(10)", "Trim leading zeros; foreign key validation against LFA1", "NOT NULL; DQ-015"),
    ("MAP-AP-002", "Accounts Payable", "LFA1.NAME1", "Vendor Name", "VENDOR_DIM.vendor_name", "VARCHAR(100)", "Direct string transfer; normalize uppercase", "NOT NULL"),
    ("MAP-AP-003", "Accounts Payable", "BSEG.ZFBDT", "Baseline Date for Due Date", "AP_OPEN_ITEMS.baseline_date", "DATE", "Convert YYYYMMDD to ISO-8601; base for payment aging", "NOT NULL"),
    ("MAP-AP-004", "Accounts Payable", "BSEG.ZBD1T", "Cash Discount Days 1", "AP_OPEN_ITEMS.net_due_days", "INTEGER", "Derive due date: baseline_date + ZBD1T days", "NULLABLE"),
    ("MAP-AP-005", "Accounts Payable", "BSEG.DMBTR", "Amount in Local Currency", "AP_OPEN_ITEMS.open_amount_inr", "DECIMAL(18,2)", "Compute remaining open balance: DMBTR - Clearing_Amount", "NOT NULL"),
    ("MAP-AP-006", "Accounts Payable", "LFA1.STCD3", "Vendor GSTIN", "VENDOR_DIM.gstin", "VARCHAR(15)", "15-char alphanumeric; Luhn mod-36 validation; PAN cross-check", "NOT NULL; DQ-005"),
    
    # DOM-03: AR
    ("MAP-AR-001", "Accounts Receivable", "BSID.KUNNR", "Customer Account Number", "AR_OPEN_ITEMS.customer_id", "VARCHAR(10)", "Trim leading zeros; foreign key lookup in KNA1", "NOT NULL"),
    ("MAP-AR-002", "Accounts Receivable", "KNA1.NAME1", "Customer Name", "CUSTOMER_DIM.customer_name", "VARCHAR(100)", "Direct string transfer; UTF-8 encoding", "NOT NULL"),
    ("MAP-AR-003", "Accounts Receivable", "BSID.DMBTR", "Invoice Amount in INR", "AR_OPEN_ITEMS.invoice_amount_inr", "DECIMAL(18,2)", "Signed balance for receivables ledger", "NOT NULL"),
    ("MAP-AR-004", "Accounts Receivable", "BSID.ZFBDT", "Baseline Date", "AR_OPEN_ITEMS.invoice_due_date", "DATE", "Calculate due date; compute Days Sales Outstanding (DSO)", "NOT NULL"),
    ("MAP-AR-005", "Accounts Receivable", "KNA1.STCD3", "Customer GSTIN", "CUSTOMER_DIM.gstin", "VARCHAR(15)", "State registration alignment with shipping destination", "NOT NULL; DQ-017"),
    
    # DOM-04: Cost Center
    ("MAP-CO-001", "Cost Center CO", "CSKS.KOSTL", "Cost Center Code", "COST_CENTER_DIM.cost_center_code", "VARCHAR(10)", "Uppercase normalized alphanumeric ID", "NOT NULL; DQ-013"),
    ("MAP-CO-002", "Cost Center CO", "CSKT.KTEXT", "Cost Center Description", "COST_CENTER_DIM.cost_center_name", "VARCHAR(40)", "Extract English language text (SPRAS = 'E')", "NOT NULL"),
    ("MAP-CO-003", "Cost Center CO", "CSKS.KOSAR", "Cost Center Category", "COST_CENTER_DIM.category_code", "VARCHAR(1)", "Map single-char category: 'P'=Prod, 'A'=Admin, 'R'=R&D", "NOT NULL"),
    ("MAP-CO-004", "Cost Center CO", "SETNODE.SETNAME", "Hierarchy Node Name", "COST_CENTER_DIM.hierarchy_l3_plant", "VARCHAR(24)", "Flatten 7-level hierarchy path for Plant node", "NOT NULL; TST-FNC-006"),
    ("MAP-CO-005", "Cost Center CO", "SETNODE.SUBSETNAME", "Department Sub-Node", "COST_CENTER_DIM.hierarchy_l5_dept", "VARCHAR(24)", "Flatten hierarchy path for Department node", "NOT NULL"),
    ("MAP-CO-006", "Cost Center CO", "COSP.WKG001", "Actual Costs Period 01", "CO_ACTUALS.actual_cost_inr", "DECIMAL(18,2)", "Aggregate period actuals for V3 financial year", "NOT NULL"),
    
    # DOM-05: Profit Center
    ("MAP-PC-001", "Profit Center CO", "CEPC.PRCTR", "Profit Center Code", "PROFIT_CENTER_DIM.profit_center_code", "VARCHAR(10)", "Trim leading zeros; lookup in active CEPC table", "NOT NULL; DQ-014"),
    ("MAP-PC-002", "Profit Center CO", "CEPCT.KTEXT", "Profit Center Description", "PROFIT_CENTER_DIM.profit_center_name", "VARCHAR(40)", "Language filtered (SPRAS='E')", "NOT NULL"),
    ("MAP-PC-003", "Profit Center CO", "CEPC.VERAK", "Person Responsible", "PROFIT_CENTER_DIM.responsible_manager", "VARCHAR(20)", "Direct transfer", "NULLABLE"),
    ("MAP-PC-004", "Profit Center CO", "CEPC.SEGMENT", "Operating Segment", "PROFIT_CENTER_DIM.segment_code", "VARCHAR(10)", "Map to corporate business segment (EV, Powertrain, Tooling)", "NOT NULL"),
    ("MAP-PC-005", "Profit Center CO", "CEPC.DATBI", "Valid To Date", "PROFIT_CENTER_DIM.valid_to_date", "DATE", "Convert YYYYMMDD to ISO date; must be >= BUDAT", "NOT NULL; DQ-014"),
    
    # DOM-06: MM / Purchasing
    ("MAP-MM-001", "Procurement MM", "EKKO.EBELN", "Purchasing Document Number", "PURCHASE_ORDERS.po_number", "VARCHAR(10)", "Direct alphanumeric transfer", "NOT NULL; TST-FNC-007"),
    ("MAP-MM-002", "Procurement MM", "EKPO.EBELP", "PO Item Number", "PURCHASE_ORDERS.po_item_number", "INTEGER", "Convert CHAR(5) to integer", "NOT NULL"),
    ("MAP-MM-003", "Procurement MM", "EKPO.MATNR", "Material Number", "PURCHASE_ORDERS.material_id", "VARCHAR(18)", "Trim leading zeros", "NOT NULL"),
    ("MAP-MM-004", "Procurement MM", "EKPO.MENGE", "PO Quantity", "PURCHASE_ORDERS.order_quantity", "DECIMAL(13,3)", "Preserve 3 decimal precision", "NOT NULL"),
    ("MAP-MM-005", "Procurement MM", "EKPO.NETPR", "Net Order Price", "PURCHASE_ORDERS.unit_price_inr", "DECIMAL(15,2)", "Normalized to currency INR", "NOT NULL"),
    ("MAP-MM-006", "Procurement MM", "MSEG.MENGE", "Quantity in Goods Receipt", "GR_IR_MATCH.gr_received_quantity", "DECIMAL(13,3)", "3-way match validation against PO and IR", "NOT NULL"),
    
    # DOM-07: SD / Sales
    ("MAP-SD-001", "Sales & Dist", "VBAK.VBELN", "Sales Document Number", "SALES_ORDERS.sales_order_id", "VARCHAR(10)", "Direct transfer", "NOT NULL"),
    ("MAP-SD-002", "Sales & Dist", "VBAP.POSNR", "Sales Document Item", "SALES_ORDERS.item_number", "INTEGER", "Convert CHAR(6) to integer", "NOT NULL"),
    ("MAP-SD-003", "Sales & Dist", "VBAK.KUNNR", "Sold-To Party", "SALES_ORDERS.customer_id", "VARCHAR(10)", "Foreign key to CUSTOMER_DIM", "NOT NULL"),
    ("MAP-SD-004", "Sales & Dist", "VBAP.NETWR", "Net Value of Item", "SALES_ORDERS.net_amount_inr", "DECIMAL(15,2)", "Transaction amount before tax", "NOT NULL"),
    ("MAP-SD-005", "Sales & Dist", "VBAP.MWSBP", "Tax Amount in INR", "SALES_ORDERS.total_tax_inr", "DECIMAL(15,2)", "3-way split: CGST+SGST or IGST", "NOT NULL; DQ-018"),
    
    # DOM-08: Fixed Assets
    ("MAP-AA-001", "Fixed Assets", "ANLA.ANLN1", "Main Asset Number", "FIXED_ASSETS_DIM.asset_id", "VARCHAR(12)", "Trim leading zeros; main asset register ID", "NOT NULL"),
    ("MAP-AA-002", "Fixed Assets", "ANLA.ANLN2", "Asset Sub-Number", "FIXED_ASSETS_DIM.sub_asset_id", "VARCHAR(4)", "Sub-component asset index", "NOT NULL"),
    ("MAP-AA-003", "Fixed Assets", "ANLA.AKTIV", "Asset Capitalization Date", "FIXED_ASSETS_DIM.capitalization_date", "DATE", "Convert YYYYMMDD to ISO date", "NOT NULL"),
    ("MAP-AA-004", "Fixed Assets", "ANLA.KANSW", "Asset Acquisition Value", "FIXED_ASSETS_DIM.acquisition_cost_inr", "DECIMAL(18,2)", "Historic gross acquisition value", "NOT NULL"),
    ("MAP-AA-005", "Fixed Assets", "ANLP.NAFAG", "Ordinary Depreciation Posted", "DEPRECIATION_FACT.depreciation_amount_inr", "DECIMAL(18,2)", "Cannot exceed acquisition cost", "NOT NULL; DQ-024"),
    
    # DOM-09: Cash & Banking
    ("MAP-CM-001", "Treasury & Cash", "FEBKO.KUKEY", "Short Key for Bank Statement", "BANK_STATEMENTS.statement_batch_id", "VARCHAR(8)", "Unique bank statement import key", "NOT NULL"),
    ("MAP-CM-002", "Treasury & Cash", "FEBEP.ESNUM", "Line Item in Statement", "BANK_STATEMENTS.statement_line_id", "INTEGER", "Convert CHAR(5) to integer", "NOT NULL"),
    ("MAP-CM-003", "Treasury & Cash", "FEBEP.KWERT", "Transaction Amount in INR", "BANK_STATEMENTS.clearing_amount_inr", "DECIMAL(18,2)", "Signed bank line amount", "NOT NULL"),
    ("MAP-CM-004", "Treasury & Cash", "FEBEP.VALUT", "Value Date", "BANK_STATEMENTS.value_date", "DATE", "Convert YYYYMMDD to ISO date", "NOT NULL"),
    ("MAP-CM-005", "Treasury & Cash", "FEBEP.CHECT", "Cheque / UTR Reference Number", "BANK_STATEMENTS.bank_reference_utr", "VARCHAR(30)", "Match against RTGS/NEFT clearing entries", "NULLABLE; TST-FNC-008"),
    
    # DOM-10: Currency & FX
    ("MAP-FX-001", "Currency & FX", "TCURR.KURST", "Exchange Rate Type", "EXCHANGE_RATES_DIM.rate_type", "VARCHAR(4)", "Filter for standard mid-market rate 'M'", "NOT NULL"),
    ("MAP-FX-002", "Currency & FX", "TCURR.FCURR", "From Currency", "EXCHANGE_RATES_DIM.source_currency", "VARCHAR(3)", "ISO-4217 code (USD, EUR, GBP, JPY)", "NOT NULL; DQ-008"),
    ("MAP-FX-003", "Currency & FX", "TCURR.TCURR", "To Currency", "EXCHANGE_RATES_DIM.target_currency", "VARCHAR(3)", "Base reporting currency 'INR'", "NOT NULL; DQ-008"),
    ("MAP-FX-004", "Currency & FX", "TCURR.GDATU", "Inverted Date Format", "EXCHANGE_RATES_DIM.rate_date", "DATE", "Compute effective date: 99999999 - GDATU", "NOT NULL"),
    ("MAP-FX-005", "Currency & FX", "TCURR.UKURS", "Exchange Rate", "EXCHANGE_RATES_DIM.exchange_rate", "DECIMAL(12,5)", "Handle indirect quotation inversion: if UKURS < 0 then 1/abs(UKURS)", "NOT NULL; DQ-010")
]

for row_idx, row_data in enumerate(mappings_54, start=2):
    for col_idx, val in enumerate(row_data, start=1):
        cell = ws_master.cell(row=row_idx, column=col_idx, value=val)
        cell.font = regular_font
        cell.border = thin_border
        if col_idx in (1, 2, 6):
            cell.alignment = Alignment(horizontal="center")

# Auto-adjust column widths
for col in range(1, 9):
    col_letter = get_column_letter(col)
    max_len = max(len(str(ws_master.cell(row=r, column=col).value or '')) for r in range(1, len(mappings_54)+2))
    ws_master.column_dimensions[col_letter].width = max(max_len + 3, 14)

wb.save(excel_path)
print(f"Successfully generated {excel_path} with {len(mappings_54)} mappings!")
