"use client";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard, MessageSquare, FileText, HelpCircle,
  Database, Building2, Users, ScrollText, LogOut, ClipboardCheck, BarChart3,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { BrandLogo } from "@/components/BrandLogo";
import { getSidebarSections, SidebarItemKey } from "@/lib/navigation-policy";

const icons: Record<SidebarItemKey, typeof LayoutDashboard> = {
  overview: LayoutDashboard,
  assistant: MessageSquare,
  documents: FileText,
  faq: HelpCircle,
  database: Database,
  evaluations: ClipboardCheck,
  analytics: BarChart3,
  organizations: Building2,
  users: Users,
  audit: ScrollText,
};

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const sections = getSidebarSections(user?.role);

  const NavItem = ({ item }: { item: { key: SidebarItemKey; name: string; href: string } }) => {
    const active = pathname === item.href;
    const Icon = icons[item.key];
    return (
      <Link
        href={item.href}
        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
          active
            ? "bg-red-600 text-white shadow-lg shadow-red-600/30"
            : "text-slate-300 hover:bg-white/10 hover:text-white"
        }`}
      >
        <Icon size={18} />
        {item.name}
      </Link>
    );
  };

  return (
    <aside className="w-64 min-h-screen flex flex-col" style={{ background: "#1a1a2e" }}>
      <div className="p-5 border-b border-white/10">
        <BrandLogo variant="sidebar" />
      </div>

      <nav className="flex-1 p-3 space-y-6 overflow-y-auto">
        {sections.map((section) => (
          <div key={section.label}>
            <p className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">{section.label}</p>
            <div className="space-y-1">
              {section.items.map((item) => <NavItem key={item.href} item={item} />)}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-3 border-t border-white/10">
        <div className="px-3 py-2 mb-2">
          <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
          <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-semibold uppercase rounded-full bg-red-600/20 text-red-400">
            {user?.role?.replace("_", " ")}
          </span>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
