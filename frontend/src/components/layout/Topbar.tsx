"use client";
import { Bell, Menu } from "lucide-react";
import { LanguageSwitch } from "@/components/LanguageSwitch";
import { useI18n } from "@/lib/i18n-context";

export default function Topbar({ onMenuClick }: { onMenuClick?: () => void }) {
  const { t } = useI18n();
  return (
    <header className="h-14 border-b border-slate-200 bg-white flex items-center justify-between px-3 md:px-6">
      <button type="button" onClick={onMenuClick} aria-label={t("navigation.openMenu")} className="p-2 text-slate-500 hover:text-slate-700 rounded-lg hover:bg-slate-100 md:hidden">
        <Menu size={20} />
      </button>
      <div className="flex items-center gap-3">
        <LanguageSwitch />
        <button aria-label={t("navigation.notifications")} className="relative p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}
