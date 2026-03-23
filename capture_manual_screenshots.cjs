const fs = require("node:fs/promises");
const path = require("node:path");

const { chromium } = require("playwright");

const FRONTEND_URL = "http://127.0.0.1:3000";
const BACKEND_LOGIN_URL = "http://127.0.0.1:8000/api/auth/login";
const COMPANIES_URL = "http://127.0.0.1:8000/api/companies";
const OUTPUT_DIR = "/Users/123ang/andai-runtime/local_llm/manual_screenshots";
const EMAIL = "admin@askai.local";
const PASSWORD = "admin123";

async function login() {
  const response = await fetch(BACKEND_LOGIN_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      username: EMAIL,
      password: PASSWORD,
    }),
  });

  if (!response.ok) {
    throw new Error(`Login failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

async function getCompanies(token) {
  const response = await fetch(COMPANIES_URL, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

async function ensureLoaded(page, headingText) {
  await page.waitForLoadState("networkidle");
  if (headingText) {
    await page.getByRole("heading", { name: headingText }).waitFor({ timeout: 20000 });
  }
  await page.waitForTimeout(1200);
}

async function capture(page, targetPath, options = {}) {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
  await page.screenshot({
    path: targetPath,
    fullPage: options.fullPage ?? true,
  });
  console.log(`Captured ${targetPath}`);
}

async function main() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });

  const { access_token: token, user } = await login();
  const companies = await getCompanies(token);
  const firstCompany = companies[0] || null;

  const browser = await chromium.launch({
    headless: true,
    channel: "chrome",
  });

  const context = await browser.newContext({
    viewport: { width: 1600, height: 1200 },
    deviceScaleFactor: 2,
  });

  const page = await context.newPage();

  // 01 Login page
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1200);
  await capture(page, `${OUTPUT_DIR}/01-login.png`);

  // Seed local auth + company selection for the protected pages.
  await page.evaluate(
    ({ token: authToken, authUser, companyId }) => {
      localStorage.setItem("token", authToken);
      localStorage.setItem("user", JSON.stringify(authUser));
      if (companyId) {
        localStorage.setItem("askai_selected_company_id", String(companyId));
      }
    },
    { token, authUser: user, companyId: firstCompany ? firstCompany.id : user.company_id }
  );

  // 02 Overview
  await page.goto(`${FRONTEND_URL}/dashboard`, { waitUntil: "domcontentloaded" });
  await ensureLoaded(page, "Welcome back, " + user.full_name);
  await capture(page, `${OUTPUT_DIR}/02-overview.png`);

  // 03 Assistant
  await page.goto(`${FRONTEND_URL}/dashboard/assistant`, { waitUntil: "domcontentloaded" });
  await page.getByPlaceholder("Ask about your data, documents, or policies...").waitFor({ timeout: 20000 });
  await page.waitForTimeout(1200);
  await capture(page, `${OUTPUT_DIR}/03-assistant.png`);

  // 04 Documents
  await page.goto(`${FRONTEND_URL}/dashboard/documents`, { waitUntil: "domcontentloaded" });
  await ensureLoaded(page, "Documents");
  await capture(page, `${OUTPUT_DIR}/04-documents.png`);

  // 05 FAQ
  await page.goto(`${FRONTEND_URL}/dashboard/faq`, { waitUntil: "domcontentloaded" });
  await ensureLoaded(page, "FAQ");
  await capture(page, `${OUTPUT_DIR}/05-faq.png`);

  // 06 Database tables
  await page.goto(`${FRONTEND_URL}/dashboard/database`, { waitUntil: "domcontentloaded" });
  await ensureLoaded(page, "Database");
  await capture(page, `${OUTPUT_DIR}/06-database-tables.png`);

  // 07 Database upload tab
  await page.getByRole("button", { name: "Upload Table & Data" }).click();
  await page.waitForTimeout(1200);
  await capture(page, `${OUTPUT_DIR}/07-database-upload.png`);

  // 08 Companies
  await page.goto(`${FRONTEND_URL}/dashboard/companies`, { waitUntil: "domcontentloaded" });
  await ensureLoaded(page, "Companies");
  await capture(page, `${OUTPUT_DIR}/08-companies.png`);

  // 09 Users
  await page.goto(`${FRONTEND_URL}/dashboard/users`, { waitUntil: "domcontentloaded" });
  await ensureLoaded(page, "Users");
  await capture(page, `${OUTPUT_DIR}/09-users.png`);

  // 10 Audit Logs
  await page.goto(`${FRONTEND_URL}/dashboard/audit`, { waitUntil: "domcontentloaded" });
  await ensureLoaded(page, "Audit Logs");
  await capture(page, `${OUTPUT_DIR}/10-audit-logs.png`);

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
