import { describe, it, expect } from 'vitest';
import { STRATEGY_PRESETS } from './presets';

describe('Strategy Builder Presets', () => {
  it('loads all builtin presets with valid ids and titles', () => {
    expect(STRATEGY_PRESETS.length).toBeGreaterThan(0);
    for (const preset of STRATEGY_PRESETS) {
      expect(preset.id).toBeTruthy();
      expect(preset.title).toBeTruthy();
      expect(preset.config).toBeDefined();
      expect(preset.config.minScore).toBeGreaterThanOrEqual(6);
      expect(preset.config.minRr).toBeGreaterThanOrEqual(1.5);
    }
  });

  it('contains valid ICT and SMC presets', () => {
    const silverBullet = STRATEGY_PRESETS.find((p) => p.id === 'preset_ict_silver_bullet');
    expect(silverBullet).toBeDefined();
    expect(silverBullet?.config.key).toBe('ict_silver_bullet_pm');
    expect(silverBullet?.config.aiConfirmation).toBe(true);
  });
});

