# run the py app normall after carefully updating the path to the data folder in the code below. The code will validate the extracted records and print a summary report.
import json
from pathlib import Path
from collections import Counter

folder = Path(
    r"D:\6. Training\Ai Dude - Agent training"
    r"\SE-AI-B12-1_Buildathon_Oct2026"
    r"\SE-AI-B12_Buildathon_Oct2026"
    r"\data\raw"
)

json_file = folder / "agrisnet_schemes.json"
report_file = folder / "extraction_report.json"

records = json.loads(json_file.read_text(encoding="utf-8"))
report = json.loads(report_file.read_text(encoding="utf-8"))

print(f"Total records: {len(records)}")

fields = [
    "department",
    "scheme",
    "input_type",
    "component",
    "scheme_description",
    "subsidy",
    "eligibility",
    "documents_required",
]

print("\nField completeness:")
for field in fields:
    populated = sum(
        1 for record in records
        if record.get(field) not in (None, "", [], {})
    )
    print(
        f"{field:25} "
        f"{populated:4}/{len(records)} "
        f"({populated / max(len(records), 1) * 100:.1f}%)"
    )

keys = [
    (
        r.get("department"),
        r.get("scheme"),
        r.get("input_type"),
        r.get("component"),
    )
    for r in records
]

counts = Counter(keys)
duplicates = sum(count - 1 for count in counts.values())

print(f"\nUnique filter combinations: {len(counts)}")
print(f"Duplicate records: {duplicates}")

print("\nExtraction report:")
print(f"Combinations checked: {report.get('combinations_checked')}")
print(f"Records saved: {report.get('unique_records_saved')}")
print(f"Failure count: {report.get('failure_count')}")

print("\nFirst two records:")
print(json.dumps(records[:2], ensure_ascii=False, indent=2))
