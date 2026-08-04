"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import en from "@/locales/en.json";
import ms from "@/locales/ms.json";

export type Language = "en" | "ms";
type Values = Record<string, string | number | null | undefined>;
type I18nContextValue = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string, values?: Values) => string;
  formatDate: (value: string | number | Date, options?: Intl.DateTimeFormatOptions) => string;
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string;
};

const STORAGE_KEY = "andai-interface-language";
const dictionaries = { en, ms } as const;
const I18nContext = createContext<I18nContextValue | null>(null);

const lookup = (language: Language, key: string) => {
  let value: unknown = dictionaries[language];
  for (const part of key.split(".")) {
    if (!value || typeof value !== "object" || !(part in value)) return key;
    value = (value as Record<string, unknown>)[part];
  }
  return typeof value === "string" ? value : key;
};

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");
  const [storageReady, setStorageReady] = useState(false);

  useEffect(() => {
    let saved: string | null = null;
    try { saved = window.localStorage.getItem(STORAGE_KEY); } catch {}
    const restore = window.setTimeout(() => {
      if (saved === "en" || saved === "ms") setLanguage(saved);
      setStorageReady(true);
    }, 0);
    return () => window.clearTimeout(restore);
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    if (!storageReady) return;
    try { window.localStorage.setItem(STORAGE_KEY, language); } catch {}
  }, [language, storageReady]);

  const value = useMemo<I18nContextValue>(() => ({
    language,
    setLanguage,
    t: (key, values = {}) => Object.entries(values).reduce(
      (text, [name, replacement]) => text.replaceAll(`{${name}}`, String(replacement ?? "")),
      lookup(language, key),
    ),
    formatDate: (date, options) => new Intl.DateTimeFormat(language === "ms" ? "ms-MY" : "en-MY", options).format(new Date(date)),
    formatNumber: (number, options) => new Intl.NumberFormat(language === "ms" ? "ms-MY" : "en-MY", options).format(number),
  }), [language]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside LanguageProvider");
  return value;
}
