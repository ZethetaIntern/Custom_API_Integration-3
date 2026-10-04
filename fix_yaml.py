import re
import yaml

filepath = r"c:\Users\USER\OneDrive\Desktop\Custom_API_Integration\FDE-9B-[YourName]-Batch01\api-specs\openapi-finsight-v2.yaml"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    m = re.match(r"^(\s*(?:description|summary|title):\s+)(.*)$", line)
    if m:
        prefix, val = m.group(1), m.group(2).strip()
        if (": " in val or "`" in val or "{" in val or "[" in val) and not (val.startswith('"') and val.endswith('"')) and not (val.startswith("'") and val.endswith("'")) and val not in ("|", ">-", ">"):
            clean_val = val.replace('"', '\\"')
            line = f'{prefix}"{clean_val}"\n'
    new_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

# Test YAML parsing
try:
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    print("YAML successfully parsed! Total paths:", len(data.get("paths", {})))
except Exception as e:
    print("Error parsing YAML:", e)
