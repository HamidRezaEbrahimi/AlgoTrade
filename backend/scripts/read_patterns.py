"""Deep analysis of pattern configs and ML data for comparison with AlgoTrade engine."""
import json
import os
import sys
from pathlib import Path

import yaml

# Add backend directory to sys.path so app modules can be imported
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Localized paths relative to AlgoTrade project backend (Single Source of Truth)
try:
    from app.config import get_settings
    settings = get_settings()
    CONFIG_DIR = str(settings.pattern_config_dir)
    ML_DIR = str(settings.ml_patterns_dir)
except Exception:
    CONFIG_DIR = str(BACKEND_DIR / "config" / "patterns")
    ML_DIR = str(BACKEND_DIR / "data" / "datasets" / "ml_patterns")

names = [
    "regular_flat", "expanded_flat", "running_flat",
    "contract_flat", "complex_flat", "flag", "wedge", "curve_correction"
]

print("=" * 80)
print("PATTERN DEFINITIONS - GEOMETRY, RULES, DECISION MODEL")
print("=" * 80)

for name in names:
    path = os.path.join(CONFIG_DIR, f"{name}.yaml")
    if not os.path.exists(path):
        print(f"\n=== {name} === FILE NOT FOUND")
        continue
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f)

    print(f"\n{'='*60}")
    print(f"  PATTERN: {name}")
    print(f"{'='*60}")

    # Pattern metadata
    pat = d.get("pattern", {})
    print(f"  name_en: {pat.get('name_en')}")
    print(f"  group: {pat.get('group')}")

    # Geometry
    geo = d.get("geometry", {})
    print("\n  GEOMETRY:")
    print(f"    point_count: {geo.get('point_count')}")
    print(f"    segments: {json.dumps(geo.get('segments'), ensure_ascii=False, indent=6) if geo.get('segments') else 'None'}")

    # Rules  
    rules = d.get("rules", {})
    print("\n  RULES:")
    print(f"    {json.dumps(rules, ensure_ascii=False, indent=4)[:2000]}")

    # Decision model
    dm = d.get("decision_model", {})
    print("\n  DECISION MODEL:")
    if dm:
        print(f"    order: {dm.get('order')}")
        steps = dm.get("steps", dm.get("decisions", []))
        if steps:
            for step in steps[:5]:
                print(f"    - step: {json.dumps(step, ensure_ascii=False)[:200]}")

    # Outcome scenarios (first 3)
    scenarios = d.get("outcome_scenarios", [])
    if scenarios:
        print(f"\n  OUTCOME SCENARIOS (first 3 of {len(scenarios)}):")
        for sc in scenarios[:3]:
            sid = sc.get("id", "?")
            conds = sc.get("conditions_cel", {}).get("all", [])
            print(f"    {sid}: {conds}")

print("\n\n" + "=" * 80)
print("ML PATTERN SAMPLES - WAVE STRUCTURE")
print("=" * 80)

# Read a few diverse ML samples
samples = [
    r"FXCM_XAUUSD\FXCM_XAUUSD_60min_20260319_0630_regular_flat.json",
    r"FXCM_XAUUSD\FXCM_XAUUSD_5min_20260304_2210_expanded_flat.json",
    r"FXCM_XAUUSD\FXCM_XAUUSD_5min_20260224_1740_running_flat.json",
    r"FXCM_XAUUSD\FXCM_XAUUSD_5min_20260302_0845_flag.json",
]

for sp in samples:
    fp = os.path.join(ML_DIR, sp)
    if not os.path.exists(fp):
        print(f"\n--- {sp} --- NOT FOUND")
        continue
    with open(fp, encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"\n--- {os.path.basename(sp)} ---")
    print(f"  pattern_key: {data.get('pattern_key')}")
    print(f"  is_valid: {data.get('is_valid')}")
    print(f"  is_completed: {data.get('is_completed')}")
    print(f"  direction: {data.get('direction', data.get('meta', {}).get('direction'))}")
    
    waves = data.get("waves", [])
    print(f"  waves ({len(waves)}):")
    for w in waves:
        wname = w.get("name", "?")
        wrole = w.get("wave_role", "?")
        wtype = w.get("wave_type", "?")
        candles = w.get("candles", [])
        if candles:
            first_c = candles[0]
            last_c = candles[-1]
            prices = [c.get("high", 0) for c in candles] + [c.get("low", 0) for c in candles]
            print(f"    {wname} (role={wrole}, type={wtype}): {len(candles)} candles, high={max(prices):.2f}, low={min(prices):.2f}")
    
    outcome = data.get("outcome", {})
    if outcome:
        print(f"  outcome: {json.dumps(outcome, ensure_ascii=False)[:300]}")
