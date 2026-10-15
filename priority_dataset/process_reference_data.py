
import json
from pathlib import Path

# Input and output file paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "priority_dataset" / "reference_dataset.json"
OUTPUT_PATH = BASE_DIR / "priority_dataset" / "processed_dataset.json"

# Read the original JSON file
with open(DATASET_PATH, "r", encoding="utf-8") as file:
    records = json.load(file)

# Modify each record
modified_records = []

for index, record in enumerate(records, start=1):
    # Remove the location key
    record.pop("location", None)

    # Add ID as the first key
    record = {
        "id": f"ref_{index:03d}",
        **record
    }

    modified_records.append(record)

# Write the modified records to a new JSON file
with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    json.dump(modified_records, file, indent=2, ensure_ascii=False)

print(f"Successfully processed {len(modified_records)} records.")
print(f"Output saved to: {OUTPUT_PATH}")