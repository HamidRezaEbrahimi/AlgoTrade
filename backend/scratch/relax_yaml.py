import re

with open('G:/Project/AlgoTrade/backend/data/pattern_rules.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace p4_above_p0
content = re.sub(r'condition:\s*\"p4_price\s*>\s*p0_price\"', 'condition: "p4_vs_p0_atr > -0.5"', content)
content = re.sub(r'condition:\s*\"p4_price\s*<\s*p0_price\"', 'condition: "p4_vs_p0_atr > -0.5"', content)

# Relax c_breaks_p2
content = re.sub(r'condition:\s*\"c_drop\s*>\s*a_drop\"', 'condition: "c_drop > a_drop * 0.8"', content)
content = re.sub(r'condition:\s*\"c_rise\s*>\s*a_rise\"', 'condition: "c_rise > a_rise * 0.8"', content)

# Relax retrace bounds for flats
content = re.sub(r'condition:\s*\"retrace_total\s*>\s*flag_max_ret\"', 'condition: "retrace_total > 0.236"', content)

# Write back
with open('G:/Project/AlgoTrade/backend/data/pattern_rules.yaml', 'w', encoding='utf-8') as f:
    f.write(content)
