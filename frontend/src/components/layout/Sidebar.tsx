"use client";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard, MessageSquare, FileText, HelpCircle,
  Database, Building2, Users, ScrollText, LogOut, Bot,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

const mainNav = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Assistant", href: "/dashboard/assistant", icon: MessageSquare },
];

const adminNav = [
  { name: "Documents", href: "/dashboard/documents", icon: FileText },
  { name: "FAQ", href: "/dashboard/faq", icon: HelpCircle },
  { name: "Database", href: "/dashboard/database", icon: Database },
];

const platformNav = [
  { name: "Companies", href: "/dashboard/companies", icon: Building2 },
  { name: "Users", href: "/dashboard/users", icon: Users },
  { name: "Audit Logs", href: "/dashboard/audit", icon: ScrollText },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout, isAdmin, isSuperAdmin } = useAuth();

  const NavItem = ({ item }: { item: (typeof mainNav)[0] }) => {
    const active = pathname === item.href;
    return (
      <Link
        href={item.href}
        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
          active
            ? "bg-red-600 text-white shadow-lg shadow-red-600/30"
            : "text-slate-300 hover:bg-white/10 hover:text-white"
        }`}
      >
        <item.icon size={18} />
        {item.name}
      </Link>
    );
  };

  return (
    <aside className="w-64 min-h-screen flex flex-col" style={{ background: "#1a1a2e" }}>
      <div className="p-5 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Bot size={28} className="text-red-500" />
          <span className="text-xl font-bold text-white tracking-tight">AskAI</span>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-6 overflow-y-auto">
        <div>
          <p className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Main</p>
          <div className="space-y-1">
            {mainNav.map((item) => <NavItem key={item.href} item={item} />)}
          </div>
        </div>

        {isAdmin && (
          <div>
            <p className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Administration</p>
            <div className="space-y-1">
              {adminNav.map((item) => <NavItem key={item.href} item={item} />)}
            </div>
          </div>
        )}

        {isSuperAdmin && (
          <div>
            <p className="px-3 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Platform</p>
            <div className="space-y-1">
              {platformNav.map((item) => <NavItem key={item.href} item={item} />)}
            </div>
          </div>
        )}
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
