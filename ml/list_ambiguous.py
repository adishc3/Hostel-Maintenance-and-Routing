import pandas as pd

df = pd.read_csv('ml/dataset/electrical_keyword_matches.csv')
keys = ['light','lamp','fan','switch','socket','outlet','power','electric','wiring','appliance','motor','pump','flicker','flickering']
mask = df['hostel_category'] != 'Electrical'
mask &= df['complaint'].str.lower().str.contains('|'.join(keys))
amb = df[mask]
amb.to_csv('ml/dataset/ambiguous_electrical_examples.csv', index=False)
print('Wrote', len(amb), 'ambiguous examples to ml/dataset/ambiguous_electrical_examples.csv')
print(amb[['id','complaint','hostel_category','category']].head(30).to_string(index=False))
