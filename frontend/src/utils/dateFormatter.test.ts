import { describe, it, expect } from 'vitest';
import { toPersianDigits, formatGregorianDate } from './dateFormatter';

describe('dateFormatter utils', () => {
  it('converts english digits to persian digits', () => {
    expect(toPersianDigits(12345)).toBe('۱۲۳۴۵');
    expect(toPersianDigits('09876')).toBe('۰۹۸۷۶');
    expect(toPersianDigits('Score: 8/8')).toBe('Score: ۸/۸');
  });

  it('formats timestamp to Gregorian YYYY-MM-DD correctly', () => {
    // 1700000000 = 2023-11-14T22:13:20Z
    const ts = 1700000000;
    expect(formatGregorianDate(ts)).toBe('2023-11-14');
  });

  it('handles invalid or empty timestamps gracefully', () => {
    expect(formatGregorianDate(0)).toBe('---');
    expect(formatGregorianDate(NaN)).toBe('---');
  });
});
