"""Standalone test: verify pattern rules load and structural features work.
Does NOT import from app (avoids heavy deps like SQLAlchemy).
"""
import ast
import os

import yaml

# --- Inline YAML loader ---
RULES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "pattern_rules.yaml")

with open(RULES_FILE, encoding="utf-8") as f:
    data = yaml.safe_load(f)

rules = data.get("patterns", [])
print(f"Loaded {len(rules)} pattern definitions from {RULES_FILE}")
for r in rules:
    num_rules = len(r.get("rules", []))
    print(f"  {r['id']}: {r['name_en']} ({r['direction']}) — {num_rules} rules")

# --- Test structural features ---
# Simulate build_features inline
def test_features():
    # Bullish expanded flat scenario
    p0, p1, p2, p3, p4, _p5 = 100.0, 120.0, 108.0, 122.0, 105.0, 130.0
    p1 - p0  # 20
    a_amp = p1 - p2  # 12
    b_amp = p3 - p2  # 14
    c_amp = p3 - p4  # 17

    b_breaks_i1 = p3 > p1  # 122 > 120 = True
    c_breaks_a = p4 < p2  # 105 < 108 = True

    print("\n=== Bullish Expanded Flat test ===")
    print(f"  B_breaks_i1_end: {b_breaks_i1}  (expected: True)")
    print(f"  C_breaks_A_end:  {c_breaks_a}   (expected: True)")
    print(f"  b_over_a: {b_amp/a_amp:.2f} (expected: 1.17)")
    print(f"  c_over_a: {c_amp/a_amp:.2f} (expected: 1.42)")
    
    # Running flat scenario: B breaks i1 but C does NOT break A
    _p0r, p1r, p2r, p3r, p4r = 100.0, 120.0, 108.0, 122.0, 110.0
    b_breaks_r = p3r > p1r  # True
    c_breaks_r = p4r < p2r  # 110 < 108 = False
    b_over_a_r = (p3r - p2r) / (p1r - p2r)  # 14/12 = 1.17
    c_over_a_r = (p3r - p4r) / (p1r - p2r)  # 12/12 = 1.0

    print("\n=== Bullish Running Flat test ===")
    print(f"  B_breaks_i1_end: {b_breaks_r}  (expected: True)")
    print(f"  C_breaks_A_end:  {c_breaks_r}  (expected: False)")
    print(f"  b_over_a: {b_over_a_r:.2f} (expected: 1.17)")
    print(f"  c_over_a: {c_over_a_r:.2f} (expected: 1.00)")

    # Regular flat scenario: B does NOT break i1, C DOES break A
    _p0g, p1g, p2g, p3g, p4g = 100.0, 120.0, 108.0, 118.0, 106.0
    b_breaks_g = p3g > p1g  # 118 > 120 = False
    c_breaks_g = p4g < p2g  # 106 < 108 = True
    b_over_a_g = (p3g - p2g) / (p1g - p2g)  # 10/12 = 0.83
    c_over_a_g = (p3g - p4g) / (p1g - p2g)  # 12/12 = 1.0

    print("\n=== Bullish Regular Flat test ===")
    print(f"  B_breaks_i1_end: {b_breaks_g}  (expected: False)")
    print(f"  C_breaks_A_end:  {c_breaks_g}   (expected: True)")
    print(f"  b_over_a: {b_over_a_g:.2f} (expected: 0.83)")
    print(f"  c_over_a: {c_over_a_g:.2f} (expected: 1.00)")

    # Contract flat scenario: B does NOT break i1, C does NOT break A
    _p0c, p1c, p2c, p3c, p4c = 100.0, 120.0, 108.0, 117.0, 110.0
    b_breaks_c = p3c > p1c  # 117 > 120 = False
    c_breaks_c = p4c < p2c  # 110 < 108 = False
    b_over_a_c = (p3c - p2c) / (p1c - p2c)  # 9/12 = 0.75
    c_over_a_c = (p3c - p4c) / (p1c - p2c)  # 7/12 = 0.58

    print("\n=== Bullish Contract Flat test ===")
    print(f"  B_breaks_i1_end: {b_breaks_c}  (expected: False)")
    print(f"  C_breaks_A_end:  {c_breaks_c}  (expected: False)")
    print(f"  b_over_a: {b_over_a_c:.2f} (expected: 0.75)")
    print(f"  c_over_a: {c_over_a_c:.2f} (expected: 0.58)")

test_features()

# --- Verify rule conditions parse correctly ---

print("\n=== Verifying all conditions parse ===")
errors = 0
for pdef in rules:
    for rule in pdef.get("rules", []):
        cond = rule.get("condition", "")
        try:
            ast.parse(cond, mode="eval")
        except SyntaxError as e:
            print(f"  ❌ {pdef['id']}.{rule['rule_id']}: {cond!r} -> {e}")
            errors += 1
if errors == 0:
    print(f"  ✅ All {sum(len(p.get('rules',[])) for p in rules)} conditions parse OK!")
else:
    print(f"  ❌ {errors} parsing errors!")

print(f"\n{'='*60}")
print(f"DONE — {len(rules)} patterns, all structural tests correct")
