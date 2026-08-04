"use client";

import { useI18n } from "@/lib/i18n-context";

export function LanguageSwitch({ dark = false }: { dark?: boolean }) {
  const { language, setLanguage, t } = useI18n();
  return (
    <div className={`grid grid-cols-2 w-[70px] h-8 p-0.5 rounded-lg border ${dark ? "border-white/20 bg-white/10" : "border-slate-200 bg-slate-100"}`} role="group" aria-label={t("common.language")}>
      {(["en", "ms"] as const).map((value) => (
        <button key={value} type="button" aria-pressed={language === value} title={t(value === "en" ? "common.english" : "common.malay")}
          onClick={() => setLanguage(value)}
          className={`rounded-md text-[11px] font-bold transition-colors ${language === value ? (dark ? "bg-white text-slate-900" : "bg-slate-900 text-white") : (dark ? "text-slate-300" : "text-slate-500")}`}>
          {value === "en" ? "EN" : "BM"}
        </button>
      ))}
    </div>
  );
}
