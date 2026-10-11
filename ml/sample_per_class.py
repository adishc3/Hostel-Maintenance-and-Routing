import pandas as pd
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "ml" / "dataset"

csv_path = DATA_DIR / "dataset_hostel.csv"
out_dir = DATA_DIR
df = pd.read_csv(csv_path)

# verify exact duplicates removed
before = len(pd.read_csv(ROOT / 'hotel_maintenance_dataset.csv'))
after = len(df)
print(f"Original rows: {before}, after dedupe: {after}")

samples = []
for cat in df['hostel_category'].unique():
    sub = df[df['hostel_category'] == cat]
    n = min(20, len(sub))
    sampled = sub.sample(n=n, random_state=42)
    samples.append(sampled[['id','complaint','category','hostel_category']])

out = pd.concat(samples, ignore_index=True)
out_file = out_dir / 'sampled_20_per_class.csv'
out.to_csv(out_file, index=False)
print(f"Saved samples to {out_file}")
print(out.groupby('hostel_category').size())

# Print samples for quick review
for _, r in out.iterrows():
    print('\n---')
    print(f"ID: {r['id']} | category: {r['category']} | hostel_category: {r['hostel_category']}")
    print(r['complaint'])
