const {
  deepEqual: navigationDeepEqual,
  equal: navigationEqual,
  ok: navigationOk,
} = require("node:assert/strict");
const { readFileSync: navigationReadFileSync } = require("node:fs");
const { join: navigationJoin } = require("node:path");
const { getSidebarSections: navigationSections } = require("../src/lib/navigation-policy.ts");

const companyHookSource = navigationReadFileSync(
  navigationJoin(process.cwd(), "src/hooks/useCompanyId.ts"),
  "utf8"
);

navigationOk(
  companyHookSource.includes('if (user?.role !== "super_admin") return user?.company_id ?? null;'),
  "organization users must ignore a company selection left by another account"
);

const flattenNames = (role: string) =>
  navigationSections(role).flatMap((section: { items: Array<{ name: string }> }) =>
    section.items.map((item) => item.name)
  );

navigationDeepEqual(flattenNames("user"), ["Assistant"]);

navigationDeepEqual(flattenNames("super_admin"), [
  "Overview",
  "Organizations",
  "Users",
  "Audit Logs",
]);

navigationEqual(flattenNames("super_admin").includes("Assistant"), false);
navigationEqual(flattenNames("user").includes("Documents"), false);
navigationEqual(flattenNames("user").includes("Organizations"), false);

navigationDeepEqual(flattenNames("admin"), [
  "Overview",
  "Assistant",
  "Documents",
  "FAQ",
  "Database",
  "Evaluations",
  "Analytics",
  "Users",
  "Audit Logs",
]);

console.log("navigation_policy_ok");
