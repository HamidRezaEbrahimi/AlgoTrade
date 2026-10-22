from tests.test_pattern_rules import _candles_from_path, _BULL_FLAG_PATH
from app.strategy.patterns.wave_classifier import _is_local_extreme, calc_atr, is_clean_impulse, extract_wave_cycle, build_features
from app.strategy.patterns.rule_engine import RuleEngine, get_detector_config, resolve_impulse_min_pct, get_pattern_rules
import numpy as np

candles = _candles_from_path(_BULL_FLAG_PATH)
detector_cfg = get_detector_config()
impulse_min_pct = resolve_impulse_min_pct(detector_cfg, None)
highs = np.array([float(c.high) for c in candles], dtype=float)
lows = np.array([float(c.low) for c in candles], dtype=float)
closes = np.array([float(c.close) for c in candles], dtype=float)
timestamps = [int(c.timestamp.timestamp()) for c in candles]
n = len(candles)
atr = calc_atr(highs, lows, closes, period=14)

ext_arr = lows
opp_arr = highs
print(f"Total candles: {n}, atr: {atr}")
for i in range(2, n - 8):
    if not _is_local_extreme(ext_arr, i, 2, False, n):
        continue
    for j in range(i + 3, min(n - 4, i + 20)):
        if not _is_local_extreme(opp_arr, j, 2, True, n):
            continue
        disp = opp_arr[j] - ext_arr[i]
        impulse_atr = calc_atr(highs[i:j+1], lows[i:j+1], closes[i:j+1])
        clean = is_clean_impulse(highs, lows, i, j, impulse_atr, 'bullish')
        cycle = extract_wave_cycle(highs, lows, timestamps, n, i, j, 'bullish')
        print(f"i={i}, j={j}, disp={disp:.2f}, clean={clean}, cycle={cycle is not None}")
        if cycle:
            features = build_features(cycle, atr, detector_cfg, impulse_min_pct)
            engine = RuleEngine()
            pat, evals = engine.classify(features, 'bullish')
            print(f"Classify result: {pat.get('id') if pat else None}")
            if not pat:
                for p in get_pattern_rules():
                    if p.get('direction') == 'bullish':
                        failed = [r['rule_id'] for r in p.get('rules', []) if not engine.evaluate_rule(r, features).passed]
                        print(f"  {p['id']} failed rules: {failed}")
