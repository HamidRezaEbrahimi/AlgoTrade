# backend/scratch/update_alef_trade.py
"""Updates AlefTrade running_flat.py and SKILL.md with P0 invalidation and progressive scanning."""

rf_path = 'G:/Projects/AlefTrade/patterns/running_flat.py'
with open(rf_path, 'r', encoding='utf-8') as f:
    rf_code = f.read()

# Add scan_progressive_developing method to RunningFlatDetector if not present
if "def scan_progressive_developing(" not in rf_code:
    prog_method = '''
    def scan_progressive_developing(
        self,
        df: pd.DataFrame,
        pivots: List[PivotPoint],
        timeframe: Optional[str] = None,
    ) -> Optional[DevelopingWave]:
        """
        Candle-by-candle progressive wave tracker from 3 pivots (P0->P1->A).
        Guards against P0 breach and detects zero-lag PRZ reversals.
        """
        if len(pivots) < 3 or len(df) < 5:
            return None

        cur_bar = len(df) - 1
        cur_close = float(df["close"].iloc[-1])
        cur_open = float(df["open"].iloc[-1])

        for i in range(len(pivots) - 1, 1, -1):
            cand_p0 = pivots[i - 2]
            cand_p1 = pivots[i - 1]
            cand_p2 = pivots[i]

            # Bearish Running Flat Setup (P0 High -> P1 Low -> P2 High A)
            if cand_p0.p_type == PivotType.HIGH and cand_p1.p_type == PivotType.LOW and cand_p2.p_type == PivotType.HIGH:
                imp_l = cand_p0.price - cand_p1.price
                wa_l = cand_p2.price - cand_p1.price
                if imp_l <= 0 or not (self.config.min_retr_a <= (wa_l / imp_l) <= self.config.max_retr_a):
                    continue
                if float(df.iloc[cand_p0.bar_idx:]["high"].max()) > cand_p0.price:
                    continue

                a_bar = cand_p2.bar_idx
                df_since_a = df.iloc[a_bar:]
                min_low_val = float(df_since_a["low"].min())
                min_low_idx = int(df_since_a["low"].idxmin())
                wb_l = cand_p2.price - min_low_val
                r_b = wb_l / wa_l if wa_l > 0 else 0.0

                if min_low_val >= cand_p1.price or r_b < self.config.min_retr_b:
                    return DevelopingWave(
                        stage="WAVE_A_FORMED", direction=PatternDirection.BEARISH,
                        p0=cand_p0, p1=cand_p1, p2=cand_p2, cur_ext_bar=a_bar,
                        cur_ext_price=cand_p2.price, prz_top=0.0, prz_bottom=0.0, current_retr=wa_l / imp_l,
                        status_text=f"ایمپالس و موج A تشکیل شد ({(wa_l/imp_l)*100:.1f}%)؛ در انتظار شکست P1",
                        is_invalidated=False,
                    )

                if self.config.min_retr_b <= r_b <= self.config.max_retr_b:
                    prz_b = min_low_val + (wb_l * self.config.min_retr_c)
                    prz_t = min(cand_p2.price, min_low_val + (wb_l * self.config.max_retr_c))
                    df_since_b = df.iloc[min_low_idx:]
                    max_high_val = float(df_since_b["high"].max())
                    max_high_idx = int(df_since_b["high"].idxmax())
                    wc_l = max_high_val - min_low_val
                    r_c = wc_l / wb_l if wb_l > 0 else 0.0
                    t_b = int(df["timestamp"].iloc[min_low_idx]) if "timestamp" in df.columns else None
                    p_b = PivotPoint(min_low_idx, min_low_val, PivotType.LOW, timestamp=t_b)

                    if max_high_val <= min_low_val + 0.3:
                        return DevelopingWave(
                            stage="WAVE_B_FORMING", direction=PatternDirection.BEARISH,
                            p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b, cur_ext_bar=min_low_idx,
                            cur_ext_price=min_low_val, prz_top=prz_t, prz_bottom=prz_b, current_retr=r_b,
                            status_text=f"موج B در حال شکست P1 ({r_b*100:.1f}%)", is_invalidated=False,
                        )

                    if r_c < self.config.min_retr_c:
                        return DevelopingWave(
                            stage="WAVE_C_FORMING", direction=PatternDirection.BEARISH,
                            p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b, cur_ext_bar=max_high_idx,
                            cur_ext_price=max_high_val, prz_top=prz_t, prz_bottom=prz_b, current_retr=r_c,
                            status_text=f"موج C در حال حرکت به سمت PRZ ({r_c*100:.1f}%)", is_invalidated=False,
                        )

                    if self.config.min_retr_c <= r_c <= self.config.max_retr_c:
                        is_reversal = (cur_close < max_high_val - 0.2) or (cur_close < cur_open) or (max_high_idx < cur_bar)
                        return DevelopingWave(
                            stage="PRZ_REVERSAL_TRIGGERED" if is_reversal else "PRZ_REVERSAL_ZONE",
                            direction=PatternDirection.BEARISH,
                            p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b, cur_ext_bar=max_high_idx,
                            cur_ext_price=max_high_val, prz_top=prz_t, prz_bottom=prz_b, current_retr=r_c,
                            status_text="سیگنال ورود قطعی در PRZ فعال شد ⚡" if is_reversal else f"موج C در محدوده شکار PRZ ({r_c*100:.1f}%)",
                            is_invalidated=False,
                        )

            # Bullish Running Flat Setup (P0 Low -> P1 High -> P2 Low A)
            elif cand_p0.p_type == PivotType.LOW and cand_p1.p_type == PivotType.HIGH and cand_p2.p_type == PivotType.LOW:
                imp_l = cand_p1.price - cand_p0.price
                wa_l = cand_p1.price - cand_p2.price
                if imp_l <= 0 or not (self.config.min_retr_a <= (wa_l / imp_l) <= self.config.max_retr_a):
                    continue
                if float(df.iloc[cand_p0.bar_idx:]["low"].min()) < cand_p0.price:
                    continue

                a_bar = cand_p2.bar_idx
                df_since_a = df.iloc[a_bar:]
                max_high_val = float(df_since_a["high"].max())
                max_high_idx = int(df_since_a["high"].idxmax())
                wb_l = max_high_val - cand_p2.price
                r_b = wb_l / wa_l if wa_l > 0 else 0.0

                if max_high_val <= cand_p1.price or r_b < self.config.min_retr_b:
                    return DevelopingWave(
                        stage="WAVE_A_FORMED", direction=PatternDirection.BULLISH,
                        p0=cand_p0, p1=cand_p1, p2=cand_p2, cur_ext_bar=a_bar,
                        cur_ext_price=cand_p2.price, prz_top=0.0, prz_bottom=0.0, current_retr=wa_l / imp_l,
                        status_text=f"ایمپالس و موج A تشکیل شد ({(wa_l/imp_l)*100:.1f}%)؛ در انتظار شکست P1",
                        is_invalidated=False,
                    )

                if self.config.min_retr_b <= r_b <= self.config.max_retr_b:
                    prz_t = max_high_val - (wb_l * self.config.min_retr_c)
                    prz_b = max(cand_p2.price, max_high_val - (wb_l * self.config.max_retr_c))
                    df_since_b = df.iloc[max_high_idx:]
                    min_low_val = float(df_since_b["low"].min())
                    min_low_idx = int(df_since_b["low"].idxmin())
                    wc_l = max_high_val - min_low_val
                    r_c = wc_l / wb_l if wb_l > 0 else 0.0
                    t_b = int(df["timestamp"].iloc[max_high_idx]) if "timestamp" in df.columns else None
                    p_b = PivotPoint(max_high_idx, max_high_val, PivotType.HIGH, timestamp=t_b)

                    if min_low_val >= max_high_val - 0.3:
                        return DevelopingWave(
                            stage="WAVE_B_FORMING", direction=PatternDirection.BULLISH,
                            p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b, cur_ext_bar=max_high_idx,
                            cur_ext_price=max_high_val, prz_top=prz_t, prz_bottom=prz_b, current_retr=r_b,
                            status_text=f"موج B در حال شکست P1 ({r_b*100:.1f}%)", is_invalidated=False,
                        )

                    if r_c < self.config.min_retr_c:
                        return DevelopingWave(
                            stage="WAVE_C_FORMING", direction=PatternDirection.BULLISH,
                            p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b, cur_ext_bar=min_low_idx,
                            cur_ext_price=min_low_val, prz_top=prz_t, prz_bottom=prz_b, current_retr=r_c,
                            status_text=f"موج C در حال حرکت به سمت PRZ ({r_c*100:.1f}%)", is_invalidated=False,
                        )

                    if self.config.min_retr_c <= r_c <= self.config.max_retr_c:
                        is_reversal = (cur_close > min_low_val + 0.2) or (cur_close > cur_open) or (min_low_idx < cur_bar)
                        return DevelopingWave(
                            stage="PRZ_REVERSAL_TRIGGERED" if is_reversal else "PRZ_REVERSAL_ZONE",
                            direction=PatternDirection.BULLISH,
                            p0=cand_p0, p1=cand_p1, p2=cand_p2, p3=p_b, cur_ext_bar=min_low_idx,
                            cur_ext_price=min_low_val, prz_top=prz_t, prz_bottom=prz_b, current_retr=r_c,
                            status_text="سیگنال ورود قطعی در PRZ فعال شد ⚡" if is_reversal else f"موج C در محدوده شکار PRZ ({r_c*100:.1f}%)",
                            is_invalidated=False,
                        )
        return None
'''
    rf_code += "\n" + prog_method
    with open(rf_path, 'w', encoding='utf-8') as f:
        f.write(rf_code)
    print("running_flat.py updated with scan_progressive_developing!")
else:
    print("scan_progressive_developing already in running_flat.py.")

# 3. Update SKILL.md in AlefTrade with comprehensive learning documentation
skill_path = 'G:/Projects/AlefTrade/.agents/skills/running-flat-pattern/SKILL.md'
with open(skill_path, 'r', encoding='utf-8') as f:
    skill_code = f.read()

new_sections = '''
---

## ۹. قانون قطعی نقض تراز P0 و چرخه حیات الگو (Deterministic P0 Lifecycle)

در تمامی انواع الگوهای امواج الیوت در AlefTrade، **تراز شروع ایمپالس اول (P0)** سقف یا کف قطعی و غیرقابل نفوذ ساختار محسوب می‌شود:

1. **الگوی صعودی (Bullish):**
   * تراز `P0` کف مطلق ساختار است.
   * هر کندلی پس از نقطه ورود C که کف آن به زیر `P0.price` نفوذ کند (`low < P0.price`)، الگو فوراً و ۱۰۰٪ **باطل شده (`INVALIDATED`)** و از هرگونه ستاپ معاملاتی خارج می‌گردد.
2. **الگوی نزولی (Bearish):**
   * تراز `P0` سقف مطلق ساختار است.
   * هر کندلی پس of C که سقف آن از `P0.price` عبور کند (`high > P0.price`)، الگو فوراً **باطل شده (`INVALIDATED`)** خواهد بود.
3. **تحقق تارگت سود (TARGET_HIT):**
   * چنانچه قیمت پیش از رسیدن به P0 به سطح تارگت اول `TP1` برسد، وضعیت به `TARGET_HIT` ارتقا یافته و الگو با پیروزی بسته می‌شود.

---

## ۱۰. ماتریس استخراج ویژگی‌ها جهت آموزش هوش مصنوعی (ML Feature Extraction)

جهت یادگیری ماشین و آموزش مدل‌های پیش‌بینی، هر الگوی کشف‌شده متد `pattern.to_feature_vector()` را ارائه می‌دهد:

| شاخص عددی | بازه استاندارد | نقش در آموزش هوش مصنوعی |
| :--- | :--- | :--- |
| `retr_a` | 0.15 - 0.85 | میزان عمق اصلاح اولیه نسبت به ایمپالس |
| `retr_b` | 1.02 - 2.50 | قدرت انبساط و هانت نقدینگی سقف/کف P1 |
| `retr_c` | 0.60 - 1.05 | میزان بازگشت به باکس شکار معامله (PRZ) |
| `slope_ratio` | >= 1.00 | نسبت زمان/شیب موج اصلاحی به ایمپالس |
| `er_b` | <= 0.40 | شاخص کارایی کافمن (تشخیص چاپی بودن موج B) |
| `chop_b` | 38.2 - 61.8 | شاخص شاپی بودن ساختار |
| `dtw_score` | 0.00 - 0.35 | فاصله اعوجاج زمانی نسبت به الگوی ایده‌آل |

**برچسب هدف آموزش (Target Label):**
- برچسب `1`: الگو به تارگت اول رسید (`TARGET_HIT`).
- برچسب `0`: الگو با نفوذ به تراز P0 استاپ خورد (`INVALIDATED`).

---

## ۱۱. دفترچه آموزه‌ها و تغییرات (Changelog v1.1.0)
- **نسخه ۱.۱.۰ (اکتبر ۲۰۲۶)**:
  - انتقال رسمی متد `evaluate_lifecycle(df)` به ساختار `PatternResult` در هسته AlefTrade.
  - اضافه شدن متد `to_feature_vector()` جهت اتصال مستقیم به خط لوله یادگیری ماشین.
  - تعریف گارد قطعی نفوذ به تراز P0 برای هر دو جهت صعودی و نزولی.
  - پیاده‌سازی متد `scan_progressive_developing` برای پایش بدون تاخیر از ۳ پیوت به جای انتظار برای ۴ پیوت.
'''

if "## ۹. قانون قطعی نقض تراز P0" not in skill_code:
    # Replace Changelog section
    if "## ۸. دفترچه یادداشت آموزه‌ها" in skill_code:
        idx = skill_code.find("## ۸. دفترچه یادداشت آموزه‌ها")
        skill_code = skill_code[:idx].strip() + "\n" + new_sections
    else:
        skill_code = skill_code.strip() + "\n" + new_sections
    with open(skill_path, 'w', encoding='utf-8') as f:
        f.write(skill_code)
    print("SKILL.md in AlefTrade successfully updated!")
else:
    print("SKILL.md already up-to-date.")
