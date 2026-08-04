const { ok: uploadGuardOk } = require("node:assert/strict");
const { readFileSync: uploadGuardReadFile } = require("node:fs");
const { join: uploadGuardJoin } = require("node:path");

const uploadGuardAuthSource = uploadGuardReadFile(
  uploadGuardJoin(process.cwd(), "src/lib/auth-context.tsx"),
  "utf8"
);
const uploadGuardApiSource = uploadGuardReadFile(
  uploadGuardJoin(process.cwd(), "src/lib/api.ts"),
  "utf8"
);
const uploadGuardDocumentsSource = uploadGuardReadFile(
  uploadGuardJoin(process.cwd(), "src/app/dashboard/documents/page.tsx"),
  "utf8"
);

uploadGuardOk(
  uploadGuardAuthSource.includes('localStorage.removeItem("askai_selected_company_id")'),
  "login and logout must clear a company selection left by another account"
);
uploadGuardOk(
  uploadGuardAuthSource.includes('data.user.role !== "super_admin"') &&
    uploadGuardAuthSource.includes(
      'localStorage.setItem("askai_selected_company_id", String(data.user.company_id))'
    ),
  "organization users must store the company returned by login"
);
uploadGuardOk(
  uploadGuardApiSource.includes('localStorage.removeItem("askai_selected_company_id")'),
  "automatic 401 cleanup must clear the selected company"
);
uploadGuardOk(
  uploadGuardDocumentsSource.includes('window.addEventListener("beforeunload"') &&
    uploadGuardDocumentsSource.includes('window.removeEventListener("beforeunload"'),
  "document upload must warn before leaving or refreshing"
);
uploadGuardOk(
  uploadGuardDocumentsSource.includes("fixed inset-0 z-50") &&
    uploadGuardDocumentsSource.includes("Uploading document") &&
    uploadGuardDocumentsSource.includes("Please keep this page open until the upload completes."),
  "document upload must render a full-screen blocking loader"
);
uploadGuardOk(
  uploadGuardDocumentsSource.includes("finally") &&
    uploadGuardDocumentsSource.includes("setUploading(false)"),
  "document upload must always remove the blocking state"
);

console.log("upload_guard_policy_ok");
