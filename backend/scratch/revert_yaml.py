import re

with open('G:/Project/AlgoTrade/backend/data/pattern_rules.yaml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

current_direction = 'bullish'

for i, line in enumerate(lines):
    if 'direction: "bullish"' in line:
        current_direction = 'bullish'
    elif 'direction: "bearish"' in line:
        current_direction = 'bearish'
    
    if 'p4_vs_p0_atr >' in line:
        if current_direction == 'bullish':
            lines[i] = re.sub(r'\"p4_vs_p0_atr\s*>\s*-[0-9.]+\"', '"p4_price > p0_price"', line)
        else:
            lines[i] = re.sub(r'\"p4_vs_p0_atr\s*>\s*-[0-9.]+\"', '"p4_price < p0_price"', line)
            
    if 'p2_vs_p0_atr >' in line:
        if current_direction == 'bullish':
            lines[i] = re.sub(r'\"p2_vs_p0_atr\s*>\s*-[0-9.]+\"', '"p2_price > p0_price"', line)
        else:
            lines[i] = re.sub(r'\"p2_vs_p0_atr\s*>\s*-[0-9.]+\"', '"p2_price < p0_price"', line)
            
    if 'c_drop > a_drop * 0.8' in line:
        lines[i] = line.replace('c_drop > a_drop * 0.8', 'c_drop > a_drop')
        
    if 'c_rise > a_rise * 0.8' in line:
        lines[i] = line.replace('c_rise > a_rise * 0.8', 'c_rise > a_rise')
        
    if 'retrace_total > 0.236' in line:
        lines[i] = line.replace('retrace_total > 0.236', 'retrace_total > flag_max_ret')

with open('G:/Project/AlgoTrade/backend/data/pattern_rules.yaml', 'w', encoding='utf-8') as f:
    f.writelines(lines)
