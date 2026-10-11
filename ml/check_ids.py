import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / 'ml' / 'dataset' / 'dataset_hostel.csv')
ids = [102,3,1490,226,645,293,134,900,1367,909,72,668,992,430]
for i in ids:
    row = df[df['id']==i]
    if len(row):
        print(i, row.iloc[0]['complaint'], '->', row.iloc[0]['hostel_category'])
    else:
        print(i, 'NOT FOUND')
