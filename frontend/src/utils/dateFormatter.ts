/**
 * Shamsi (Jalali) & Gregorian Dual Date Formatter for Charts & Trading UI.
 * Pure native Intl implementation with zero external dependencies.
 */

// Persian digits converter
export const toPersianDigits = (num: number | string): string => {
  const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  return String(num).replace(/\d/g, (d) => persianDigits[parseInt(d, 10)]);
};

// Formats timestamp in seconds to Shamsi date string (e.g. "۱۴۰۴/۰۶/۰۳")
export const formatShamsiDate = (tsInSeconds: number, usePersianDigits = true): string => {
  if (!tsInSeconds || isNaN(tsInSeconds)) return '---';
  const date = new Date(tsInSeconds * 1000);
  try {
    const formatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
    const str = formatter.format(date);
    return usePersianDigits ? str : str.replace(/[۰-۹]/g, (d) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)));
  } catch {
    return date.toISOString().split('T')[0];
  }
};

// Formats timestamp in seconds to Gregorian date string (e.g. "2026-08-25")
export const formatGregorianDate = (tsInSeconds: number): string => {
  if (!tsInSeconds || isNaN(tsInSeconds)) return '---';
  const date = new Date(tsInSeconds * 1000);
  const y = date.getUTCFullYear();
  const m = String(date.getUTCMonth() + 1).padStart(2, '0');
  const d = String(date.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

// Formats time in HH:MM
export const formatTimeHHMM = (tsInSeconds: number): string => {
  if (!tsInSeconds || isNaN(tsInSeconds)) return '';
  const date = new Date(tsInSeconds * 1000);
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
};

// Dual formatted string for Chart Crosshairs & Tooltips (e.g. "۱۴۰۴/۰۶/۰۳ (2026-08-25) 16:30")
export const formatDualDateTime = (tsInSeconds: number): string => {
  if (!tsInSeconds || isNaN(tsInSeconds)) return '---';
  const shamsi = formatShamsiDate(tsInSeconds, true);
  const greg = formatGregorianDate(tsInSeconds);
  const time = formatTimeHHMM(tsInSeconds);
  return `${shamsi} (${greg})${time ? ` ${time}` : ''}`;
};

// Tick mark formatter for TradingView Lightweight Charts X-axis
export const formatChartTickMark = (timePoint: any): string => {
  const ts = typeof timePoint === 'number' ? timePoint : timePoint?.timestamp || timePoint;
  if (!ts || isNaN(ts)) return '';
  const date = new Date(ts * 1000);
  try {
    const formatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      month: 'numeric',
      day: 'numeric',
    });
    return formatter.format(date);
  } catch {
    return `${date.getUTCMonth() + 1}/${date.getUTCDate()}`;
  }
};
