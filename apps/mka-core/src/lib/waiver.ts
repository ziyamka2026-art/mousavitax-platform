// محاسبه‌گر بخشودگی جرائم — پورت منطق TAXLAW-WAIVER-CALCULATOR نسخه 1.3.0
// مبنای قواعد: بخشنامه 200/1404/504 مورخ 1404/07/21 (اجرای از 1404/09/01)

export const WAIVER_VERSION = "1.3.0";
export const WAIVER_CIRCULAR_ID = "200/1404/504";

const BASE_RATES = {
  "1403+": 1.0,
  "1402": 0.95,
  "1401": 0.85,
  "1400": 0.75,
  "1399-": 0.65,
} as const;

const DEDUCTIONS = { perAppealStage: 0.05, afterExecutiveOneMonth: 0.1 };
const FLOORS = { cash: 0.3, installment: 0.2 };
const ART190 = { exemptionAcceptOrAgreement: 0.8, exemptionWithinOneMonthFinal: 0.4 };

export const SPECIAL_INCREASES = [
  {
    title: "افزایش تفویض واحدهای تولیدی و آسیب‌دیده از جنگ رمضان (1405/05/25)",
    bands: [
      { from: "1405/05/26", to: "1405/05/31", rate: 0.2 },
      { from: "1405/06/01", to: "1405/06/15", rate: 0.15 },
      { from: "1405/06/16", to: "1405/06/31", rate: 0.1 },
    ],
  },
];

export const PENALTY_TYPES = [
  "جریمه تأخیر ماده ۱۹۰",
  "جریمه ماده ۱۹۲",
  "جریمه ماده ۱۶۹",
  "جریمه بند ب ماده ۳۶ ارزش افزوده",
  "جریمه ماده ۳۷ ارزش افزوده",
  "جریمه حقوق",
  "جریمه اجاره/نقل‌وانتقال",
  "سایر قابل بخشش",
  "جرائم غیرقابل بخشش",
  "سایر",
];

export const DOC_CHECKLIST = [
  "برگ تشخیص (ابلاغ‌شده)",
  "برگ قطعی",
  "رسید پرداخت یا ترتیب پرداخت",
  "اظهارنامه تسلیمی",
  "مدارک تکالیف قانونی (دفاتر/اسناد)",
  "توافق ماده ۲۳۹ یا قبولی تشخیص",
  "مدارک واحد تولیدی",
  "مدارک آسیب‌دیدگی جنگ رمضان",
  "آرای مراحل دادرسی",
  "مدارک کاهش بدهی ≥۳۰٪",
  "برگ اجرایی و تاریخ ابلاغ",
  "خسارت تأخیر ماده ۲۴۲",
  "لیست جرائم غیرقابل بخشش",
  "وکالتنامه نماینده",
];

export type PenaltyRow = { type: string; amount: number; waivable: boolean };

export type WaiverInput = {
  year: number;
  appealStages: number;
  reduceDebt30: boolean;
  afterExecutiveOneMonth: boolean;
  payType: "پرداخت نقدی" | "ترتیب پرداخت";
  art19080: boolean;
  art19040: boolean;
  isProductionUnit: boolean;
  payDate: string; // فرمت شمسی 1405/06/01
  penalties: PenaltyRow[];
};

export type WaiverResult = {
  baseAfterDeductions: number;
  art190Rate: number;
  specialAdd: number;
  finalPct: number;
  waivableSum: number;
  nonWaivableSum: number;
  waivedAmount: number;
  remaining: number;
};

function baseRate(year: number): number {
  if (year >= 1403) return BASE_RATES["1403+"];
  if (year === 1402) return BASE_RATES["1402"];
  if (year === 1401) return BASE_RATES["1401"];
  if (year === 1400) return BASE_RATES["1400"];
  return BASE_RATES["1399-"];
}

export function calculateWaiver(inp: WaiverInput): WaiverResult {
  const base = baseRate(inp.year);
  const dedAppeal = inp.reduceDebt30 ? 0 : inp.appealStages * DEDUCTIONS.perAppealStage;
  const dedExec = inp.afterExecutiveOneMonth ? DEDUCTIONS.afterExecutiveOneMonth : 0;
  const floor = inp.payType === "پرداخت نقدی" ? FLOORS.cash : FLOORS.installment;
  const afterDed = Math.max(floor, base - dedAppeal - dedExec);

  const art190 = inp.art19080
    ? ART190.exemptionAcceptOrAgreement
    : inp.art19040
      ? ART190.exemptionWithinOneMonthFinal
      : 0;
  const afterArt = Math.max(afterDed, art190);

  let specialAdd = 0;
  if (inp.isProductionUnit && inp.payDate) {
    for (const si of SPECIAL_INCREASES) {
      for (const band of si.bands) {
        if (band.from <= inp.payDate && inp.payDate <= band.to) {
          specialAdd = Math.max(specialAdd, band.rate);
        }
      }
    }
  }

  const finalPct = Math.min(1, afterArt + specialAdd);
  const waivable = inp.penalties
    .filter((p) => p.waivable)
    .reduce((sum, p) => sum + Math.max(0, p.amount), 0);
  const nonWaivable = inp.penalties
    .filter((p) => !p.waivable)
    .reduce((sum, p) => sum + Math.max(0, p.amount), 0);
  const waived = Math.round(waivable * finalPct);

  return {
    baseAfterDeductions: afterDed,
    art190Rate: art190,
    specialAdd,
    finalPct,
    waivableSum: waivable,
    nonWaivableSum: nonWaivable,
    waivedAmount: waived,
    remaining: waivable + nonWaivable - waived,
  };
}
