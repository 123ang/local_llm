const { ok } = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");

const source = readFileSync(join(process.cwd(), "src/app/dashboard/assistant/page.tsx"), "utf8");
const databaseSource = readFileSync(join(process.cwd(), "src/app/dashboard/database/page.tsx"), "utf8");

ok(
  !source.includes('{ key: "apis"'),
  "assistant must not expose APIs as an end-user source"
);
ok(
  !source.includes("API snapshots"),
  "assistant must not describe API snapshots as knowledge evidence"
);
ok(
  !databaseSource.includes('label: "API Connectors"'),
  "database must not expose API connector controls"
);

ok(
  !source.includes("if (!input.trim() || sending || chatDepartmentIds.length === 0) return"),
  "assistant chat controls must not disable sending only because the user has no departments"
);
ok(
  !source.includes("disabled={sending || chatDepartmentIds.length === 0}"),
  "assistant input must remain enabled when the user has no departments"
);
ok(
  !source.includes("disabled={sending || !input.trim() || chatDepartmentIds.length === 0}"),
  "assistant send button must remain enabled when text is present and the user has no departments"
);
ok(
  !source.includes("No department knowledge access has been assigned yet."),
  "assistant should show a non-blocking no-department note instead of a blocking warning"
);

ok(
  !source.includes("isAdmin"),
  "assistant chat controls and diagnostics must be the same for admin and normal users"
);
ok(
  source.includes("Array.from(enabledSources),\n        aiInsights,\n        modelMode,"),
  "assistant must send the selected AI Insights and response mode for every user"
);

console.log("assistant_chat_policy_ok");
