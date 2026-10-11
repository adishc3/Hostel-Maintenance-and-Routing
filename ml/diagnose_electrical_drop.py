import pandas as pd
from pathlib import Path
import sys
# add workspace root to path so we can import ml
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.reclassify_dataset import classify_row

DATA_DIR = ROOT / "ml" / "dataset"

train_fp = DATA_DIR / "train_hostel.csv"
test_fp = DATA_DIR / "test_hostel.csv"
current_fp = DATA_DIR / "dataset_hostel.csv"
report_fp = DATA_DIR / "electrical_diagnosis_report.csv"

def norm(s):
    return (s or "").strip().lower()

train = pd.read_csv(train_fp)
test = pd.read_csv(test_fp)
prev = pd.concat([train, test], ignore_index=True)
prev["complaint_norm"] = prev["complaint"].astype(str).apply(norm)
prev = prev.drop_duplicates(subset=["complaint_norm"])

cur = pd.read_csv(current_fp)
cur["complaint_norm"] = cur["complaint_norm"].astype(str)

# merge previous hostel_category
merged = cur.merge(prev[["complaint_norm", "hostel_category"]].rename(columns={"hostel_category": "hostel_prev"}), on="complaint_norm", how="left")

# Where previous was Electrical but current is not
mask_changed = (merged["hostel_prev"] == "Electrical") & (merged["hostel_category"] != "Electrical")
changed = merged[mask_changed].copy()

# If fewer than 50, we still output all; otherwise sample first 50
examples = changed[["id", "complaint", "hostel_prev", "hostel_category", "category"]].head(500)

# Counts where previous Electrical records went
where_went = changed["hostel_category"].value_counts()

# Identify complaints containing electrical-related keywords
keywords = [
    "light", "lamp", "fan", "switch", "socket", "outlet", "power", "electric", "wiring", "appliance", "motor", "pump", "heating element",
]
def contains_any(text, kws):
    t = (text or "").lower()
    return any(k in t for k in kws)

kw_matches = merged[merged["complaint"].astype(str).apply(lambda x: contains_any(x, keywords))][["id","complaint","hostel_category","category","hostel_prev"]]

# Check canonical phrase examples using current classify_row
canonical_phrases = [
    "light not working", "fan not working", "switch broken", "power outlet not working",
    "electricity problem", "electrical wiring damaged", "appliance not working"
]
canon_results = [(p, classify_row(p, "")) for p in canonical_phrases]

# Save a CSV report
with open(report_fp, "w", encoding="utf-8") as f:
    f.write("id,complaint,prev_hostel,current_hostel,original_category\n")
    for _, r in examples.iterrows():
        f.write(f'{r.id},"{r.complaint.replace(chr(34), "'")}",{r.hostel_prev},{r.hostel_category},{r.category}\n')

print("Total previous Electrical records found in prev split:", (prev["hostel_category"] == "Electrical").sum())
print("Total that changed to non-Electrical in current dataset:", len(changed))
print("Where those changed records went (current hostel_category counts):\n", where_went.to_dict())
print("Report with examples saved to:", report_fp)
print("Examples (first 50):")
print(examples.head(50).to_string(index=False))
print("\nComplaints containing electrical keywords and their current classification (first 100):")
print(kw_matches.head(100).to_string(index=False))
print("\nCanonical phrase classification by current rules:")
for p, r in canon_results:
    print(f'"{p}" -> {r}')

print('\nDone')

if __name__ == '__main__':
    pass
