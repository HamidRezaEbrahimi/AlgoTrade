import yaml
with open('G:/Project/AlgoTrade/backend/data/pattern_rules.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)
for p in data['patterns']:
    for r in p.get('rules', []):
        if r.get('rule_id') == 'c_breaks_p2':
            print(f"{p['id']}: {r.get('condition', 'N/A')}")
