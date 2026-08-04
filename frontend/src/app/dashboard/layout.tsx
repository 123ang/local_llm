"use client";
import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import { useAuth } from "@/lib/auth-context";
import { canAccessDashboardPath, getDefaultDashboardPath } from "@/lib/navigation-policy";
import { useI18n } from "@/lib/i18n-context";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => { setMobileMenuOpen(false); }, [pathname]);

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
      return;
    }
    if (!loading && user && !canAccessDashboardPath(user.role, pathname)) {
      router.replace(getDefaultDashboardPath(user.role));
    }
  }, [user, loading, pathname, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
      </div>
    );
  }

  if (!user || !canAccessDashboardPath(user.role, pathname)) return null;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <div className="hidden md:block"><Sidebar /></div>
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button type="button" aria-label={t("navigation.closeMenu")} onClick={() => setMobileMenuOpen(false)} className="absolute inset-0 bg-slate-950/50" />
          <div className="relative h-full w-64 shadow-2xl">
            <Sidebar />
            <button type="button" aria-label={t("navigation.closeMenu")} onClick={() => setMobileMenuOpen(false)} className="absolute right-3 top-3 rounded-lg p-2 text-slate-300 hover:bg-white/10 hover:text-white">
              <X size={18} />
            </button>
          </div>
        </div>
      )}
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar onMenuClick={() => setMobileMenuOpen(true)} />
        <main className="flex-1 p-3 md:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
