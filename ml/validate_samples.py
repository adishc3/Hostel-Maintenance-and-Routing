import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'ml' / 'dataset' / 'sampled_20_per_class.csv'
df = pd.read_csv(CSV)

def contains_any(text, keywords):
    t = str(text).lower()
    return any(k in t for k in keywords)

bathwords = ['bath', 'bathroom', 'bathtub', 'toilet', 'shower', 'sink']
electoral = ['light','fan','socket','outlet','plug','power','wiring','switch','electr','flicker','flickering','shock']
plumbing = ['leak','leaking','pipe','drain','blocked','overflow','flush','hot water','water supply']

electrical_rows = df[df['hostel_category']=='Electrical']
plumbing_rows = df[df['hostel_category']=='Plumbing']
struct_rows = df[df['hostel_category']=='Structural']
general_rows = df[df['hostel_category']=='General']

print('Electrical samples containing bathroom words:')
for _,r in electrical_rows.iterrows():
    if contains_any(r['complaint'], bathwords):
        print(r['id'], r['complaint'])

print('\nPlumbing samples containing bathroom words:')
for _,r in plumbing_rows.iterrows():
    if contains_any(r['complaint'], bathwords):
        print(r['id'], r['complaint'])

print('\nStructural samples containing bathroom words:')
for _,r in struct_rows.iterrows():
    if contains_any(r['complaint'], bathwords):
        print(r['id'], r['complaint'])

print('\nGeneral samples containing electrical/light/fan/water/plumbing keywords:')
kw = electoral + plumbing + ['water','leak','leaking','drain','toilet','shampoo','fan']
for _,r in general_rows.iterrows():
    if contains_any(r['complaint'], kw):
        print(r['id'], r['complaint'])
