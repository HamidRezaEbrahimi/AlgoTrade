import React from 'react';
import { useTranslation } from 'react-i18next';
import { Layers } from 'lucide-react';
import { InfoTooltip } from './InfoTooltip';

interface Props {
  chkBos: boolean;
  setChkBos: (val: boolean) => void;
  chkOb: boolean;
  setChkOb: (val: boolean) => void;
  chkFvg: boolean;
  setChkFvg: (val: boolean) => void;
  chkSr: boolean;
  setChkSr: (val: boolean) => void;
  chkFlag: boolean;
  setChkFlag: (val: boolean) => void;
  chkFlat: boolean;
  setChkFlat: (val: boolean) => void;
  chkWedge: boolean;
  setChkWedge: (val: boolean) => void;
  chkEngulfing: boolean;
  setChkEngulfing: (val: boolean) => void;
  chkPinbar: boolean;
  setChkPinbar: (val: boolean) => void;
  chkHammer: boolean;
  setChkHammer: (val: boolean) => void;
  chkMorningStar: boolean;
  setChkMorningStar: (val: boolean) => void;
}

export const PatternLayer: React.FC<Props> = ({
  chkBos,
  setChkBos,
  chkOb,
  setChkOb,
  chkFvg,
  setChkFvg,
  chkSr,
  setChkSr,
  chkFlag,
  setChkFlag,
  chkFlat,
  setChkFlat,
  chkWedge,
  setChkWedge,
  chkEngulfing,
  setChkEngulfing,
  chkPinbar,
  setChkPinbar,
  chkHammer,
  setChkHammer,
  chkMorningStar,
  setChkMorningStar,
}) => {
  const { t } = useTranslation(['StrategyBuilder', 'Common']);

  return (
    <div className="glass-panel p-4 space-y-3 border border-white/10 rounded-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <div className="flex items-center gap-1.5">
          <div className="w-6 h-6 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-xs">
            <Layers size={13} />
          </div>
          <h3 className="text-xs font-bold text-white">{t('layer1.title')}</h3>
          <InfoTooltip
            title="لایه الگوهای پرایس‌اکشن و چارت"
            text="در این بخش می‌توانید الگوهای ساختار قیمت (SMC)، هندسی (پرچم، فلت، کنج) و کندل‌های تاییدیه ورود را به دلخواه ترکیب نمایید."
          />
        </div>
        <span className="text-[10px] text-slate-400">{t('layer1.subtitle')}</span>
      </div>

      {/* Section 1: SMC & Market Structure */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-1">
          <span className="text-[10.5px] font-bold text-cyan-400">{t('layer1.group_structure')}</span>
          <InfoTooltip
            title="ساختار بازار و اسمارت‌مانی"
            text="تشخیص جهت جریان سفارشات سازمانی، شکست ساختار (BOS)، گپ‌های ارزش منصفانه (FVG) و اردر بلاک‌های تقاضا."
          />
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-cyan-500/30 transition-all">
            <label className="flex items-center gap-2 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkBos}
                onChange={(e) => setChkBos(e.target.checked)}
                className="checkbox checkbox-xs checkbox-primary rounded"
              />
              <span className="text-slate-200 text-[11px] font-medium">{t('layer1.chk_bos')}</span>
            </label>
            <InfoTooltip
              title="شکست ساختار (BOS / CHoCH)"
              text="تشخیص ادامه روند صعودی با شکست بالاترین سقف (BOS) یا تغییر جهت روند از نزولی به صعودی (CHoCH)."
            />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-cyan-500/30 transition-all">
            <label className="flex items-center gap-2 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkOb}
                onChange={(e) => setChkOb(e.target.checked)}
                className="checkbox checkbox-xs checkbox-primary rounded"
              />
              <span className="text-slate-200 text-[11px] font-medium">{t('layer1.chk_ob')}</span>
            </label>
            <InfoTooltip
              title="اردر بلاک تقاضا (Demand OB)"
              text="آخرین کندل نزولی قبل از حرکت صعودی پرشتاب سازمانی که نقدینگی سفارشات خرید نهادی در آن تجمیع شده است."
            />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-cyan-500/30 transition-all">
            <label className="flex items-center gap-2 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkFvg}
                onChange={(e) => setChkFvg(e.target.checked)}
                className="checkbox checkbox-xs checkbox-primary rounded"
              />
              <span className="text-slate-200 text-[11px] font-medium">{t('layer1.chk_fvg')}</span>
            </label>
            <InfoTooltip
              title="گپ ارزش منصفانه (FVG Mitigation)"
              text="عدم تعادل در قیمت (عدم همپوشانی سایه کندل اول و سوم) که بازار برای پر کردن آن پولبک می‌زند."
            />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-cyan-500/30 transition-all">
            <label className="flex items-center gap-2 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkSr}
                onChange={(e) => setChkSr(e.target.checked)}
                className="checkbox checkbox-xs checkbox-primary rounded"
              />
              <span className="text-slate-200 text-[11px] font-medium">{t('layer1.chk_sr')}</span>
            </label>
            <InfoTooltip
              title="سطوح حمایت و مقاومت ۳۰ روزه"
              text="خطوط کلیدی چرخش قیمت و سطوح نقدینگی بر اساس اوج و کف‌های معتبر ماهانه."
            />
          </div>
        </div>
      </div>

      {/* Section 2: Geometric & Elliott Waves */}
      <div className="space-y-1.5 pt-0.5">
        <div className="flex items-center gap-1">
          <span className="text-[10.5px] font-bold text-amber-400">{t('layer1.group_geometry')}</span>
          <InfoTooltip
            title="الگوهای هندسی و امواج الیوت"
            text="الگوهای تکرارشونده نمودار برای تشخیص فازهای تثبیت، اصلاح امواج و بریک‌اوت‌های شتابی."
          />
        </div>
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-amber-500/30 transition-all">
            <label className="flex items-center gap-1.5 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkFlag}
                onChange={(e) => setChkFlag(e.target.checked)}
                className="checkbox checkbox-xs checkbox-warning rounded"
              />
              <span className="text-slate-200 text-[11px] font-medium">{t('layer1.chk_flag')}</span>
            </label>
            <InfoTooltip
              title="الگوی پرچم (Flag 4pt/6pt)"
              text="حرکت صعودی شتابی به همراه کانال اصلاحی کم‌شیب ۴ یا ۶ نقطه‌ای در ادامه روند."
            />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-amber-500/30 transition-all">
            <label className="flex items-center gap-1.5 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkFlat}
                onChange={(e) => setChkFlat(e.target.checked)}
                className="checkbox checkbox-xs checkbox-warning rounded"
              />
              <span className="text-slate-200 text-[11px] font-medium">{t('layer1.chk_flat')}</span>
            </label>
            <InfoTooltip
              title="امواج اصلاحی فلت (Regular Flat)"
              text="الگوی اصلاحی ۳-۳-۵ در انتهای موج C الیوت برای ورود در شروع موج ۵ پرقدرت."
            />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-amber-500/30 transition-all">
            <label className="flex items-center gap-1.5 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkWedge}
                onChange={(e) => setChkWedge(e.target.checked)}
                className="checkbox checkbox-xs checkbox-warning rounded"
              />
              <span className="text-slate-200 text-[11px] font-medium">{t('layer1.chk_wedge')}</span>
            </label>
            <InfoTooltip
              title="الگوی کنج (Wedge)"
              text="فشردگی نوسانات قیمت در یک ساختار همگرا همراه با کاهش حجم و شکست انفجاری."
            />
          </div>
        </div>
      </div>

      {/* Section 3: Candlestick Entry Triggers */}
      <div className="space-y-1.5 pt-0.5">
        <div className="flex items-center gap-1">
          <span className="text-[10.5px] font-bold text-purple-400">{t('layer1.group_candlestick')}</span>
          <InfoTooltip
            title="الگوهای کندلی تریگر ورود"
            text="کندل‌های تاییدیه قطعی در تایم‌فریم ۱ ساعته که نشان‌دهنده غلبه فوری خریداران بر فروشندگان هستند."
          />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-purple-500/30 transition-all">
            <label className="flex items-center gap-1.5 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkEngulfing}
                onChange={(e) => setChkEngulfing(e.target.checked)}
                className="checkbox checkbox-xs checkbox-secondary rounded"
              />
              <span className="text-slate-200 text-[10.5px] font-medium">{t('layer1.chk_engulfing')}</span>
            </label>
            <InfoTooltip
              title="کندل پوشای صعودی (Bullish Engulfing)"
              text="بدنه کندل صعودی کل بدنه کندل نزولی قبلی را می‌پوشاند."
            />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-purple-500/30 transition-all">
            <label className="flex items-center gap-1.5 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkPinbar}
                onChange={(e) => setChkPinbar(e.target.checked)}
                className="checkbox checkbox-xs checkbox-secondary rounded"
              />
              <span className="text-slate-200 text-[10.5px] font-medium">{t('layer1.chk_pinbar')}</span>
            </label>
            <InfoTooltip
              title="پین‌بار صعودی (Bullish Pin Bar)"
              text="کندل با سایه پایینی بلند حداقل ۲ برابر بدنه که نشان‌دهنده ریجکت شدید قیمت است."
            />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-purple-500/30 transition-all">
            <label className="flex items-center gap-1.5 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkHammer}
                onChange={(e) => setChkHammer(e.target.checked)}
                className="checkbox checkbox-xs checkbox-secondary rounded"
              />
              <span className="text-slate-200 text-[10.5px] font-medium">{t('layer1.chk_hammer')}</span>
            </label>
            <InfoTooltip
              title="کندل چکش (Hammer)"
              text="کندل کف با سایه پایینی کشیده و بدنه کوچک در بالاترین بخش دامنه نوسان."
            />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-white/5 hover:border-purple-500/30 transition-all">
            <label className="flex items-center gap-1.5 cursor-pointer flex-1 select-none">
              <input
                type="checkbox"
                checked={chkMorningStar}
                onChange={(e) => setChkMorningStar(e.target.checked)}
                className="checkbox checkbox-xs checkbox-secondary rounded"
              />
              <span className="text-slate-200 text-[10.5px] font-medium">{t('layer1.chk_morning_star')}</span>
            </label>
            <InfoTooltip
              title="ستاره صبحگاهی (Morning Star)"
              text="الگوی ۳ کندلی بازگشتی معتبر در انتهای روندهای اصلاحی."
            />
          </div>
        </div>
      </div>
    </div>
  );
};
