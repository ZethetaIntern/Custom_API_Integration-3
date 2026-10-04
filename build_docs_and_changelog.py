import os
import re

base_dir = r"c:\Users\USER\OneDrive\Desktop\Custom_API_Integration"
target_dir = os.path.join(base_dir, "FDE-9B-[YourName]-Batch01")
docs_dir = os.path.join(target_dir, "docs")
os.makedirs(docs_dir, exist_ok=True)

# Read D4_D5_D6
d456_path = os.path.join(base_dir, "D4_D5_D6_Reliability_Reconciliation_Observability.md")
with open(d456_path, "r", encoding="utf-8") as f:
    d456_content = f.read()

# Read D7_D8_D9
d789_path = os.path.join(base_dir, "D7_D8_D9_TestPlan_Runbook_StakeholderPack.md")
with open(d789_path, "r", encoding="utf-8") as f:
    d789_content = f.read()

# Extract D4
part1_start = d456_content.find("# PART 1: DELIVERABLE D4")
part2_start = d456_content.find("# PART 2: DELIVERABLE D5")
part3_start = d456_content.find("# PART 3: DELIVERABLE D6")
verify_start = d456_content.find("## VERIFICATION & ARCHITECTURAL ATTESTATION")

header = """# MERIDIAN MANUFACTURING LTD. | PRODUCTION INTEGRATION BLUEPRINT
**Document Reference:** ZET-MM-D4-PROD-2026-V1  
**Project:** Meridian ERP-to-Analytics Integration (SAP S/4HANA to FinSight 4.2)  
**Classification:** Confidential / Enterprise Production Standard  
**Revision Date:** October 2026  
**Status:** Approved for Production Deployment  

---
"""

d4_text = header + d456_content[part1_start:part2_start].strip() + "\n"
with open(os.path.join(docs_dir, "D4_Error_Handling_Framework.md"), "w", encoding="utf-8") as f:
    f.write(d4_text)

d5_header = header.replace("D4-PROD", "D5-PROD")
d5_text = d5_header + d456_content[part2_start:part3_start].strip() + "\n"
with open(os.path.join(docs_dir, "D5_Reconciliation_Data_Quality.md"), "w", encoding="utf-8") as f:
    f.write(d5_text)

d6_header = header.replace("D4-PROD", "D6-PROD")
d6_text = d6_header + d456_content[part3_start:].strip() + "\n"
with open(os.path.join(docs_dir, "D6_Monitoring_Observability_Spec.md"), "w", encoding="utf-8") as f:
    f.write(d6_text)

# Extract D7, D8, D9
mod1_start = d789_content.find("# MODULE 1: DELIVERABLE D7")
mod2_start = d789_content.find("# MODULE 2: DELIVERABLE D8")
mod3_start = d789_content.find("# MODULE 3: DELIVERABLE D9")

d7_header = header.replace("D4-PROD", "D7-TEST")
d7_text = d7_header + d789_content[mod1_start:mod2_start].strip() + "\n"
with open(os.path.join(docs_dir, "D7_Integration_Test_Plan.md"), "w", encoding="utf-8") as f:
    f.write(d7_text)

d8_header = header.replace("D4-PROD", "D8-RUNBOOK")
d8_text = d8_header + d789_content[mod2_start:mod3_start].strip() + "\n"
with open(os.path.join(docs_dir, "D8_Deployment_Runbook_Rollback.md"), "w", encoding="utf-8") as f:
    f.write(d8_text)

d9_header = header.replace("D4-PROD", "D9-STAKEHOLDER")
d9_text = d9_header + d789_content[mod3_start:].strip() + "\n"
with open(os.path.join(docs_dir, "D9_Stakeholder_Communication_Pack.md"), "w", encoding="utf-8") as f:
    f.write(d9_text)

print("Successfully written all docs D4 through D9!")
