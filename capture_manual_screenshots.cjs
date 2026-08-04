const fs = require("node:fs/promises");
const path = require("node:path");

const { chromium } = require("playwright");

const FRONTEND_URL = process.env.ASKAI_FRONTEND_URL || "http://127.0.0.1:3000";
const BACKEND_URL = process.env.ASKAI_BACKEND_URL || "http://127.0.0.1:8000";
const OUTPUT_DIR = path.join(__dirname, "docs/assets/manual_screenshots");
const CAPTURE_COMPANY = process.env.ASKAI_CAPTURE_COMPANY || "RBAC QA Organization";

function credentials(prefix) {
  const email = process.env[`${prefix}_EMAIL`];
  const password = process.env[`${prefix}_PASSWORD`];
  if (!email || !password) {
    throw new Error(`Set ${prefix}_EMAIL and ${prefix}_PASSWORD before capturing screenshots`);
  }
  return { email, password };
}

const ACCOUNTS = {
  superAdmin: credentials("ASKAI_SUPER_ADMIN"),
  orgAdmin: credentials("ASKAI_ORG_ADMIN"),
  user: credentials("ASKAI_USER"),
};

async function login({ email, password }) {
  const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });

  if (!response.ok) {
    throw new Error(`Login failed for ${email}: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function selectedCompanyId(auth) {
  if (auth.user.company_id) return auth.user.company_id;

  const response = await fetch(`${BACKEND_URL}/api/companies`, {
    headers: { Authorization: `Bearer ${auth.access_token}` },
  });
  if (!response.ok) throw new Error(`Unable to load organizations: ${response.status}`);

  const companies = await response.json();
  const selected = companies.find((company) => company.name === CAPTURE_COMPANY) || companies[0];
  if (!selected) throw new Error("No organization is available for Full Admin screenshots");
  return selected.id;
}

async function authenticatedPage(browser, account) {
  const auth = await login(account);
  const companyId = await selectedCompanyId(auth);
  const context = await browser.newContext({
    viewport: { width: 1600, height: 1200 },
    deviceScaleFactor: 1,
  });
  await context.addInitScript(
    ({ token, user, selectedCompany }) => {
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(user));
      localStorage.setItem("askai_selected_company_id", String(selectedCompany));
    },
    { token: auth.access_token, user: auth.user, selectedCompany: companyId }
  );
  return { context, page: await context.newPage(), user: auth.user };
}

async function capture(page, route, fileName, ready) {
  await page.goto(`${FRONTEND_URL}${route}`, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle");
  if (ready.kind === "heading") {
    await page.getByRole("heading", { name: ready.name, exact: false }).first().waitFor({ timeout: 20000 });
  } else {
    await page.getByPlaceholder(ready.name).waitFor({ timeout: 20000 });
  }
  await page.waitForTimeout(700);
  const target = path.join(OUTPUT_DIR, fileName);
  await page.screenshot({ path: target, fullPage: false });
  console.log(`Captured ${fileName}`);
}

async function main() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true, channel: "chrome" });

  try {
    const publicContext = await browser.newContext({
      viewport: { width: 1600, height: 1200 },
      deviceScaleFactor: 1,
    });
    const publicPage = await publicContext.newPage();
    await capture(publicPage, "/login", "01-login.png", { kind: "placeholder", name: "admin@askai.local" });
    await publicContext.close();

    const fullAdmin = await authenticatedPage(browser, ACCOUNTS.superAdmin);
    await capture(fullAdmin.page, "/dashboard", "02-full-admin-overview.png", { kind: "heading", name: "Welcome back" });
    await capture(fullAdmin.page, "/dashboard/companies", "03-full-admin-organizations.png", { kind: "heading", name: "Organizations" });
    await capture(fullAdmin.page, "/dashboard/users", "04-full-admin-users.png", { kind: "heading", name: "Users" });
    await capture(fullAdmin.page, "/dashboard/audit", "05-full-admin-audit-logs.png", { kind: "heading", name: "Audit Logs" });
    await fullAdmin.context.close();

    const orgAdmin = await authenticatedPage(browser, ACCOUNTS.orgAdmin);
    await capture(orgAdmin.page, "/dashboard", "06-org-admin-overview.png", { kind: "heading", name: "Welcome back" });
    await capture(orgAdmin.page, "/dashboard/documents", "07-org-admin-documents.png", { kind: "heading", name: "Documents" });
    await capture(orgAdmin.page, "/dashboard/faq", "08-org-admin-faq.png", { kind: "heading", name: "FAQ" });
    await capture(orgAdmin.page, "/dashboard/database", "09-org-admin-database.png", { kind: "heading", name: "Database" });
    await orgAdmin.page.getByRole("button", { name: "Upload Table & Data" }).click();
    await orgAdmin.page.waitForTimeout(700);
    await orgAdmin.page.screenshot({ path: path.join(OUTPUT_DIR, "10-org-admin-database-upload.png"), fullPage: false });
    console.log("Captured 10-org-admin-database-upload.png");
    await capture(orgAdmin.page, "/dashboard/evaluations", "11-org-admin-evaluations.png", { kind: "heading", name: "Evaluation Tests" });
    await capture(orgAdmin.page, "/dashboard/analytics", "12-org-admin-analytics.png", { kind: "heading", name: "Usage Analytics" });
    await capture(orgAdmin.page, "/dashboard/users", "13-org-admin-users.png", { kind: "heading", name: "Users" });
    await capture(orgAdmin.page, "/dashboard/audit", "14-org-admin-audit-logs.png", { kind: "heading", name: "Audit Logs" });
    await orgAdmin.context.close();

    const normalUser = await authenticatedPage(browser, ACCOUNTS.user);
    await capture(normalUser.page, "/dashboard/assistant", "15-normal-user-assistant.png", {
      kind: "placeholder",
      name: "Ask about your data, documents, or policies...",
    });
    const forbiddenLabel = normalUser.page.getByText("Documents", { exact: true });
    if (await forbiddenLabel.count()) {
      throw new Error("Normal User screenshot unexpectedly exposes administration navigation");
    }
    await normalUser.context.close();
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
