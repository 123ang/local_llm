export type UserRole = "super_admin" | "admin" | "user" | string | null | undefined;

export type SidebarItemKey =
  | "overview"
  | "assistant"
  | "documents"
  | "faq"
  | "database"
  | "evaluations"
  | "analytics"
  | "organizations"
  | "users"
  | "audit";

export interface SidebarItem {
  key: SidebarItemKey;
  name: string;
  href: string;
}

export interface SidebarSection {
  label: string;
  items: SidebarItem[];
}

const ITEMS: Record<SidebarItemKey, SidebarItem> = {
  overview: { key: "overview", name: "Overview", href: "/dashboard" },
  assistant: { key: "assistant", name: "Assistant", href: "/dashboard/assistant" },
  documents: { key: "documents", name: "Documents", href: "/dashboard/documents" },
  faq: { key: "faq", name: "FAQ", href: "/dashboard/faq" },
  database: { key: "database", name: "Database", href: "/dashboard/database" },
  evaluations: { key: "evaluations", name: "Evaluations", href: "/dashboard/evaluations" },
  analytics: { key: "analytics", name: "Analytics", href: "/dashboard/analytics" },
  organizations: { key: "organizations", name: "Organizations", href: "/dashboard/companies" },
  users: { key: "users", name: "Users", href: "/dashboard/users" },
  audit: { key: "audit", name: "Audit Logs", href: "/dashboard/audit" },
};

export function getSidebarSections(role: UserRole): SidebarSection[] {
  if (role === "super_admin") {
    return [
      { label: "Main", items: [ITEMS.overview] },
      { label: "Platform", items: [ITEMS.organizations, ITEMS.users, ITEMS.audit] },
    ];
  }

  if (role === "admin") {
    return [
      { label: "Main", items: [ITEMS.overview, ITEMS.assistant] },
      {
        label: "Administration",
        items: [
          ITEMS.documents,
          ITEMS.faq,
          ITEMS.database,
          ITEMS.evaluations,
          ITEMS.analytics,
          ITEMS.users,
          ITEMS.audit,
        ],
      },
    ];
  }

  return [{ label: "Main", items: [ITEMS.assistant] }];
}

export function getDefaultDashboardPath(role: UserRole): string {
  return role === "user" ? "/dashboard/assistant" : "/dashboard";
}

export function canAccessDashboardPath(role: UserRole, pathname: string): boolean {
  if (!pathname.startsWith("/dashboard")) return true;

  const allowedHrefs = getSidebarSections(role)
    .flatMap((section) => section.items.map((item) => item.href));

  return allowedHrefs.some((href) => pathname === href || pathname.startsWith(`${href}/`));
}
