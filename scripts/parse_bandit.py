import json

with open("docs/evidencias/sast/bandit.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total findings: {len(data['results'])}")
for r in data["results"]:
    print(f"[{r['issue_severity']}] {r['test_id']} ({r['test_name']}): {r['filename']}:{r['line_number']}")
    print(f"    Text: {r['issue_text']}")
    print(f"    Code: {r['code'].strip()}")
    print("-" * 50)

