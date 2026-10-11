import pandas as pd

train = pd.read_csv('ml/dataset/train_hostel.csv')
test = pd.read_csv('ml/dataset/test_hostel.csv')

t = set(train['complaint'].astype(str).str.strip().str.lower())
s = set(test['complaint'].astype(str).str.strip().str.lower())
common = t & s
print('train_count=', len(t))
print('test_count=', len(s))
print('overlap_count=', len(common))
if common:
    print('\nExamples:')
    for c in list(common)[:10]:
        print('---')
        print(c)
