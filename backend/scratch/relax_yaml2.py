import re

with open('G:/Project/AlgoTrade/backend/data/pattern_rules.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace p2_above_p0
content = re.sub(r'condition:\s*\"p2_price\s*>\s*p0_price\"', 'condition: "p2_vs_p0_atr > -5.0"', content)
content = re.sub(r'condition:\s*\"p2_price\s*<\s*p0_price\"', 'condition: "p2_vs_p0_atr > -5.0"', content)

# Update p4_vs_p0_atr to -5.0
content = re.sub(r'condition:\s*\"p4_vs_p0_atr\s*>\s*-0.5\"', 'condition: "p4_vs_p0_atr > -5.0"', content)

# Write back
with open('G:/Project/AlgoTrade/backend/data/pattern_rules.yaml', 'w', encoding='utf-8') as f:
    f.write(content)
