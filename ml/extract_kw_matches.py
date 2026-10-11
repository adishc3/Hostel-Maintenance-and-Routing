import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "ml" / "dataset"
current_fp = DATA_DIR / "dataset_hostel.csv"
out_fp = DATA_DIR / "electrical_keyword_matches.csv"

keywords = [
    "light", "lamp", "fan", "switch", "socket", "outlet", "power", "electric", "wiring", "appliance", "motor", "pump", "heating element",
]

def contains_any(text, kws):
    t = (text or "").lower()
    return any(k in t for k in kws)

cur = pd.read_csv(current_fp)
cur["match_kw"] = cur["complaint"].astype(str).apply(lambda x: contains_any(x, keywords))
matches = cur[cur["match_kw"]][["id","complaint","hostel_category","category"]]
matches.to_csv(out_fp, index=False)
print("Saved", len(matches), "keyword-matching rows to", out_fp)
