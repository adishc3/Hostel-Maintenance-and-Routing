import sys
from pathlib import Path
import pandas as pd
import random

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

DATA = ROOT / 'ml' / 'dataset' / 'dataset_hostel.csv'
if not DATA.exists():
    raise FileNotFoundError(DATA)

df = pd.read_csv(DATA)
print('Total records in hostel dataset:', len(df))

# Show distribution
print('\nCategory distribution:')
print(df['hostel_category'].value_counts())

# Define the keyword sets (import from reclassify if available)
from ml.reclassify_dataset import ELECTRICAL_KEYWORDS, PLUMBING_KEYWORDS, STRUCTURAL_KEYWORDS

# Flag function
def flag_row(text):
    t = str(text).lower()
    flags = []
    if any(k in t for k in ELECTRICAL_KEYWORDS):
        flags.append('ELECTRICAL_KW')
    if any(k in t for k in PLUMBING_KEYWORDS):
        flags.append('PLUMBING_KW')
    if any(k in t for k in STRUCTURAL_KEYWORDS):
        flags.append('STRUCTURAL_KW')
    return flags

# Analyze General class
general = df[df['hostel_category']=='General'].copy()
print('\nTotal General records:', len(general))

# Reproducible random sample of 50 (or less if not enough)
rnd = random.Random(42)
indices = list(general.index)
if len(indices) > 50:
    sample_idx = rnd.sample(indices, 50)
else:
    sample_idx = indices

sample = general.loc[sample_idx]

print('\nSampled General complaints (showing flags):\n')
for i, row in sample.iterrows():
    flags = flag_row(row['complaint'])
    print(f"- ID:{row.get('id','')}", f"OriginalCat:{row.get('category','')}", f"Flags:{flags}")
    print('  ', row['complaint'])

# Also print 10 representative examples from each category
print('\nRepresentative examples from each category:')
for cat in ['Electrical','Plumbing','Structural','General']:
    print(f"\nCategory: {cat}")
    subset = df[df['hostel_category']==cat]
    for i, row in subset.head(10).iterrows():
        print(f"- ID:{row.get('id','')} OriginalCat:{row.get('category','')} Priority:{row.get('priority','')}")
        print('  ', row['complaint'])

# Save sampled general to a CSV for manual review
out = ROOT / 'ml' / 'dataset' / 'sampled_general.csv'
sample.to_csv(out, index=False)
print('\nSample saved to', out)
