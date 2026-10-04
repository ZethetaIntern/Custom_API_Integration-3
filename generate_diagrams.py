import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

base_dir = r"c:\Users\USER\OneDrive\Desktop\Custom_API_Integration\FDE-9B-[YourName]-Batch01"
diag_dir = os.path.join(base_dir, "diagrams")
os.makedirs(diag_dir, exist_ok=True)

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

def draw_card(ax, x, y, w, h, bg_color, border_color, title, subtitle, items=None):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03", 
                                  facecolor=bg_color, edgecolor=border_color, linewidth=2)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.04, title, fontsize=10, fontweight='bold', ha='center', va='top', color='#0F172A')
    ax.text(x + w/2, y + h - 0.08, subtitle, fontsize=8, fontstyle='italic', ha='center', va='top', color='#475569')
    if items:
        for idx, item in enumerate(items):
            ax.text(x + 0.02, y + h - 0.13 - (idx * 0.04), f"• {item}", fontsize=7.5, color='#334155')

def draw_arrow(ax, x1, y1, x2, y2, label):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#1E293B", lw=2, mutation_scale=15))
    mid_x, mid_y = (x1 + x2)/2, (y1 + y2)/2
    ax.text(mid_x, mid_y + 0.02, label, fontsize=8, fontweight='bold', ha='center', va='bottom', 
            bbox=dict(boxstyle="square,pad=0.2", facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=1))

# 1. C4 Level 1: System Context
fig, ax = plt.subplots(figsize=(14, 9), dpi=200)
ax.set_facecolor('#F8FAFC')
fig.patch.set_facecolor('#F8FAFC')

ax.text(0.5, 0.95, "Meridian Manufacturing: C4 Level 1 - System Context Diagram", 
        fontsize=16, fontweight='bold', ha='center', va='center', color='#0F172A', transform=ax.transAxes)
ax.text(0.5, 0.91, "High-Level Financial Integration & Operational Boundaries (INR 2,400 Cr Revenue | 7 Plants)", 
        fontsize=10, fontstyle='italic', ha='center', va='center', color='#475569', transform=ax.transAxes)

draw_card(ax, 0.05, 0.50, 0.22, 0.32, '#E0F2FE', '#0284C7', "Source: SAP S/4HANA", "[Enterprise ERP - Pune DC]", 
          ["Universal Journal (ACDOCA)", "Sub-Ledgers (BSEG, BSIK)", "Master Data (CSKS, LFA1)", "ODP / RFC Interface"])

draw_card(ax, 0.38, 0.46, 0.24, 0.40, '#F1F5F9', '#3B82F6', "Integration Engine", "[Zetheta Streaming Pipeline]", 
          ["Dual-Entry Balance Reconciler", "25 Data Quality Rule Gates", "Decorrelated Jitter Backoff", "3-State Circuit Breaker", "S3 KMS Dead Letter Queue"])

draw_card(ax, 0.72, 0.50, 0.23, 0.32, '#ECFDF5', '#059669', "Target: FinSight 4.2", "[Financial Analytics - AWS]", 
          ["Real-Time Executive P&L", "Working Capital Cockpit", "Schedule III Reporting", "Bank Parity Engine"])

draw_card(ax, 0.05, 0.08, 0.22, 0.26, '#FEF3C7', '#D97706', "Meridian Finance Team", "[Plant & Corp Controllers]", 
          ["Monitors book close", "Reviews daily cash position", "Audits balance breaks"])

draw_card(ax, 0.72, 0.08, 0.23, 0.26, '#FEE2E2', '#DC2626', "Statutory Authorities", "[GSTN & MCA Compliance]", 
          ["GSTR-2B Recon Parity", "Companies Act 7-Yr Audit", "Zero-Variance Tax Filing"])

draw_arrow(ax, 0.27, 0.66, 0.38, 0.66, "Delta Extract (ODP)")
draw_arrow(ax, 0.62, 0.66, 0.72, 0.66, "Micro-Batch (mTLS)")
draw_arrow(ax, 0.16, 0.34, 0.16, 0.50, "Enters Journals")
draw_arrow(ax, 0.50, 0.46, 0.16, 0.22, "Audit Alerts")
draw_arrow(ax, 0.83, 0.50, 0.83, 0.34, "Statutory Reports")

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(diag_dir, "DGM_C4_L1_SystemContext.png"), dpi=200)
plt.close()

# 2. C4 Level 2: Container Diagram
fig, ax = plt.subplots(figsize=(15, 10), dpi=200)
ax.set_facecolor('#F8FAFC')
fig.patch.set_facecolor('#F8FAFC')

ax.text(0.5, 0.96, "Meridian Manufacturing: C4 Level 2 - Container Architecture", 
        fontsize=16, fontweight='bold', ha='center', va='center', color='#0F172A', transform=ax.transAxes)
ax.text(0.5, 0.92, "Deployment Units, Message Queues, Cache Layers & Storage Boundaries", 
        fontsize=10, fontstyle='italic', ha='center', va='center', color='#475569', transform=ax.transAxes)

rect_onprem = patches.FancyBboxPatch((0.03, 0.15), 0.26, 0.72, boxstyle="round,pad=0.02", 
                                     facecolor='#F1F5F9', edgecolor='#64748B', linestyle='--', linewidth=2)
ax.add_patch(rect_onprem)
ax.text(0.16, 0.84, "Pune Data Centre (On-Prem)", fontsize=11, fontweight='bold', ha='center', color='#334155')

draw_card(ax, 0.05, 0.52, 0.22, 0.26, '#E0F2FE', '#0284C7', "SAP Gateway / App Server", "[ABAP / NetWeaver]",
          ["Port 3300 RFC / Port 443 OData", "Custom CDS Views (ZCDS_*)", "Pool Quota: 50 RFC Conns", "Enqueue Lock Controller"])

draw_card(ax, 0.05, 0.20, 0.22, 0.24, '#E2E8F0', '#475569', "Extractor Pod (On-Prem)", "[Python RFC Client]",
          ["Leases RFC Connection", "Spools to Local NVMe on partition", "Throttled to < 112.5 Mbps"])

rect_aws = patches.FancyBboxPatch((0.34, 0.08), 0.63, 0.80, boxstyle="round,pad=0.02", 
                                  facecolor='#EFF6FF', edgecolor='#2563EB', linestyle='--', linewidth=2)
ax.add_patch(rect_aws)
ax.text(0.65, 0.85, "AWS Asia Pacific (Mumbai) ap-south-1", fontsize=11, fontweight='bold', ha='center', color='#1D4ED8')

draw_card(ax, 0.36, 0.52, 0.20, 0.26, '#FEF9C3', '#CA8A04', "Apache Kafka Cluster", "[Message Streaming]",
          ["3x Brokers (MSK)", "Topic: sap.acdoca.raw (12P)", "Topic: backpressure.buffer", "Topic: dlq.quarantine"])

draw_card(ax, 0.60, 0.52, 0.20, 0.26, '#DCFCE7', '#16A34A', "Transformer & Recon Pods", "[Kubernetes Microservices]",
          ["V3 Calendar Mapping", "25 DQ Rules Evaluator", "Dual-Entry GL Balancer", "Circuit Breaker Wrapper"])

draw_card(ax, 0.60, 0.16, 0.20, 0.26, '#F3E8FF', '#9333EA', "Redis Master Cache", "[ElastiCache 7.2]",
          ["72h Idempotency (SETNX)", "Cost Centre Materialized Graph", "Active Token Cache"])

draw_card(ax, 0.36, 0.16, 0.20, 0.26, '#FEE2E2', '#DC2626', "Amazon S3 Dead Letter", "[Encrypted Storage]",
          ["14-Day Quarantine Retention", "AWS KMS CMK (AES-256)", "Compliance Object Lock", "7-Yr Glacier Transition"])

draw_card(ax, 0.82, 0.34, 0.13, 0.44, '#CCFBF1', '#0D9488', "FinSight 4.2 Ingest", "[REST API]",
          ["OAuth 2.0 mTLS", "P95 < 5.0s SLA", "Postgres DW Store"])

draw_arrow(ax, 0.16, 0.52, 0.16, 0.44, "RFC Lease")
draw_arrow(ax, 0.27, 0.32, 0.36, 0.65, "MPLS Encrypted (TLS 1.3)")
draw_arrow(ax, 0.56, 0.65, 0.60, 0.65, "Consume Batch")
draw_arrow(ax, 0.70, 0.52, 0.70, 0.42, "Cache Check")
draw_arrow(ax, 0.60, 0.56, 0.56, 0.29, "Quarantine (DLQ)")
draw_arrow(ax, 0.80, 0.65, 0.82, 0.65, "POST /batch")

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(diag_dir, "DGM_C4_L2_Container.png"), dpi=200)
plt.close()

# 3. C4 Level 3: Component Diagram
fig, ax = plt.subplots(figsize=(15, 9), dpi=200)
ax.set_facecolor('#F8FAFC')
fig.patch.set_facecolor('#F8FAFC')

ax.text(0.5, 0.96, "Meridian Manufacturing: C4 Level 3 - Component Architecture", 
        fontsize=16, fontweight='bold', ha='center', va='center', color='#0F172A', transform=ax.transAxes)
ax.text(0.5, 0.92, "Internal Components of Transformer & Ingestion Pipeline Worker", 
        fontsize=10, fontstyle='italic', ha='center', va='center', color='#475569', transform=ax.transAxes)

rect_worker = patches.FancyBboxPatch((0.05, 0.08), 0.90, 0.80, boxstyle="round,pad=0.02", 
                                     facecolor='#FFFFFF', edgecolor='#0F172A', linewidth=2)
ax.add_patch(rect_worker)
ax.text(0.50, 0.84, "meridian-transformer-worker:v4.2.0 (Go / Python Engine)", fontsize=12, fontweight='bold', ha='center', color='#0F172A')

draw_card(ax, 0.08, 0.48, 0.16, 0.28, '#E0F2FE', '#0284C7', "Kafka Ingress Consumer", "[Partition Listener]",
          ["Consumer Group: fin-ingest", "Batch Poller (500 records)", "Avro Deserializer"])

draw_card(ax, 0.28, 0.48, 0.18, 0.28, '#EFF6FF', '#2563EB', "Transformation Engine", "[Domain Business Logic]",
          ["Fiscal V3 Mapper", "7-Level Tree Flattener", "GST 3-Way Split Resolver", "Currency Inversion (TCURR)"])

draw_card(ax, 0.50, 0.48, 0.18, 0.28, '#FEF9C3', '#CA8A04', "Data Quality Validator", "[25 Rules Enforcement]",
          ["Null / Range Checkers", "Luhn Mod-36 GSTIN Engine", "Referential Integrity Filter", "Fatal / Critical Actions"])

draw_card(ax, 0.72, 0.48, 0.18, 0.28, '#DCFCE7', '#16A34A', "Reconciler & Egress", "[Ledger Integrity]",
          ["Dual-Entry GL Balance (0.00)", "Cryptographic Checksum", "Circuit Breaker Client", "Idempotent REST Dispatcher"])

draw_card(ax, 0.28, 0.14, 0.18, 0.24, '#F3E8FF', '#9333EA', "Resilience Subsystem", "[Failure Handling]",
          ["Jitter Backoff Calculator", "3-State Circuit State", "Spillover Queue Director"])

draw_card(ax, 0.50, 0.14, 0.18, 0.24, '#FEE2E2', '#DC2626', "DLQ Quarantine Router", "[Isolation Gateway]",
          ["Diagnostic Envelope Pack", "Payload SHA-256 Hasher", "S3 KMS Direct Uploader"])

draw_card(ax, 0.72, 0.14, 0.18, 0.24, '#CCFBF1', '#0D9488', "Structured Logger & Metrics", "[Prometheus / LogQL]",
          ["12 Mandatory Attributes", "Prometheus Counters / Latency", "Batch Certification Emitter"])

draw_arrow(ax, 0.24, 0.62, 0.28, 0.62, "Raw Records")
draw_arrow(ax, 0.46, 0.62, 0.50, 0.62, "Transformed")
draw_arrow(ax, 0.68, 0.62, 0.72, 0.62, "Validated OK")
draw_arrow(ax, 0.59, 0.48, 0.59, 0.38, "DQ Fail -> DLQ")
draw_arrow(ax, 0.81, 0.48, 0.81, 0.38, "Telemetry")
draw_arrow(ax, 0.72, 0.52, 0.46, 0.26, "Retry / Break")

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(diag_dir, "DGM_C4_L3_Component.png"), dpi=200)
plt.close()

# 4. Network Topology
fig, ax = plt.subplots(figsize=(15, 9), dpi=200)
ax.set_facecolor('#F8FAFC')
fig.patch.set_facecolor('#F8FAFC')

ax.text(0.5, 0.96, "Meridian Manufacturing: Hybrid Cloud Network Topology", 
        fontsize=16, fontweight='bold', ha='center', va='center', color='#0F172A', transform=ax.transAxes)
ax.text(0.5, 0.92, "450 Mbps Shared MPLS Link, SD-WAN Traffic Shaping & AWS VPC Ingress", 
        fontsize=10, fontstyle='italic', ha='center', va='center', color='#475569', transform=ax.transAxes)

draw_card(ax, 0.04, 0.16, 0.26, 0.68, '#F1F5F9', '#475569', "Pune On-Premises Data Centre", "[CIDR: 10.140.10.0/24]",
          ["SAP Gateway Server (10.140.10.25:3300)", "SAP Message Server (10.140.10.26:3600)", 
           "Corporate DNS Server (10.140.10.50:53)", "SD-WAN Edge Router & Traffic Shaper",
           "Bandwidth Cap: 25% (112.5 Mbps Max)", "Hardware IPsec Crypto Accelerator"])

draw_card(ax, 0.36, 0.35, 0.26, 0.34, '#FEF3C7', '#D97706', "Shared 450 Mbps MPLS Link", "[Dedicated SD-WAN Virtual Circuit]",
          ["Encrypted IPsec Tunnel (AES-256-GCM)", "Average Latency: 22ms - 26ms", 
           "Bandwidth Budget: 112.5 Mbps Integration", "Active Alerting at 100 Mbps (ALT-008)",
           "Automatic Token Bucket Rate Shaping"])

draw_card(ax, 0.68, 0.16, 0.28, 0.68, '#EFF6FF', '#2563EB', "AWS Asia Pacific (Mumbai) ap-south-1", "[VPC CIDR: 172.24.10.0/24]",
          ["AWS Transit Gateway (TGW) Endpoint", "Kubernetes EKS Cluster (meridian-etl)", 
           "MSK Kafka Brokers (Port 9092 mTLS)", "FinSight 4.2 Ingestion NLB (Port 443)",
           "AWS Secrets Manager & KMS CMK", "Amazon S3 DLQ Storage (VPC Endpoint)"])

draw_arrow(ax, 0.30, 0.52, 0.36, 0.52, "Egress IPsec")
draw_arrow(ax, 0.62, 0.52, 0.68, 0.52, "Ingress TGW")

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(diag_dir, "DGM_Network_Topology.png"), dpi=200)
plt.close()

print("All 4 architectural diagrams successfully generated!")
