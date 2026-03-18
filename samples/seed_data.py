"""
AskAI Sample Data Seed Script
==============================
Creates sample FAQ items and uploads sample CSV datasets into the first company
(company_id=1, which is the Demo Company created on first startup).

Usage:
  cd c:\\Users\\User\\Desktop\\Website\\local_llm
  python samples/seed_data.py

Requirements:
  - Backend running at http://localhost:8000
  - Admin credentials: admin@askai.local / admin123
  - (Optional) A company must exist with id=1
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@askai.local"
ADMIN_PASSWORD = "admin123"
COMPANY_ID = 1  # Demo Company

SAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))

FAQ_ITEMS = [
    {
        "question": "What are your office working hours?",
        "answer": "Our office is open Monday to Friday, 9:00 AM – 6:00 PM (local time). "
                  "We are closed on weekends and public holidays. For urgent matters, "
                  "please email support@company.com and we will respond within 24 hours.",
        "category": "General",
    },
    {
        "question": "How do I reset my account password?",
        "answer": "To reset your password: (1) Go to the login page and click 'Forgot Password'. "
                  "(2) Enter your registered email address. (3) Check your inbox for a password reset link. "
                  "(4) The link is valid for 30 minutes. If you do not receive the email, check your spam folder "
                  "or contact IT support at it-support@company.com.",
        "category": "IT Support",
    },
    {
        "question": "What is the company's annual leave policy?",
        "answer": "Full-time employees are entitled to 14 days of paid annual leave per year. "
                  "Leave accrues at 1.17 days per month. Unused leave can be carried over up to 5 days into the "
                  "next calendar year. Leave must be applied through the HR portal with at least 5 working days' "
                  "notice. Public holidays are separate and not deducted from annual leave.",
        "category": "HR Policy",
    },
    {
        "question": "How do I submit an expense claim?",
        "answer": "To submit an expense claim: (1) Collect all original receipts. (2) Log in to the Finance Portal. "
                  "(3) Select 'Expense Claims' > 'New Claim'. (4) Upload receipts and fill in the details. "
                  "(5) Submit for manager approval. Claims must be submitted within 30 days of the expense date. "
                  "Reimbursement is processed on the 15th of each month for approved claims.",
        "category": "Finance",
    },
    {
        "question": "What is the remote work policy?",
        "answer": "Employees may work remotely up to 3 days per week with manager approval. "
                  "You must be available during core hours (10 AM – 4 PM). Ensure your home network is secure "
                  "and use the company VPN at all times. Remote work is not permitted during the first 3 months "
                  "of employment. Full-remote arrangements require VP-level approval.",
        "category": "HR Policy",
    },
    {
        "question": "How do I request new IT equipment?",
        "answer": "Equipment requests must be submitted via the IT Service Desk ticket system. "
                  "Standard equipment (laptop, mouse, keyboard) is typically delivered within 5–7 business days. "
                  "Specialty equipment may take up to 3 weeks. All equipment remains company property and must be "
                  "returned upon resignation. Budget approvals are required for items over $500.",
        "category": "IT Support",
    },
    {
        "question": "What is the company's data privacy policy?",
        "answer": "We are committed to protecting personal data in accordance with GDPR and local data protection laws. "
                  "Personal data is collected only for legitimate business purposes and is never sold to third parties. "
                  "Employees have the right to access, correct, or request deletion of their personal data by contacting "
                  "privacy@company.com. Data retention periods vary by type: HR records (7 years), financial records (10 years).",
        "category": "Compliance",
    },
    {
        "question": "How do I join the company health insurance plan?",
        "answer": "New employees are automatically enrolled in the standard health insurance plan starting from their "
                  "first day of employment. To upgrade to a premium plan or add dependants, submit a request to HR "
                  "within 30 days of your start date or during the annual open enrollment period (October 1–31). "
                  "The company covers 80% of the premium; employees contribute 20% via payroll deduction.",
        "category": "Benefits",
    },
    {
        "question": "What is the process for requesting a salary review?",
        "answer": "Salary reviews are conducted annually in January. To request an out-of-cycle review, "
                  "speak with your direct manager first. If supported, your manager submits a Compensation Review "
                  "Request to HR with justification (market data, performance, scope change). Reviews typically "
                  "take 4–6 weeks. Mid-year reviews are approved only for significant role changes or promotions.",
        "category": "HR Policy",
    },
    {
        "question": "How do I report a workplace safety incident?",
        "answer": "All workplace incidents must be reported immediately, regardless of severity. "
                  "(1) Ensure the area is safe and seek medical attention if needed. "
                  "(2) Notify your direct supervisor immediately. "
                  "(3) Complete an Incident Report Form in the Safety Portal within 24 hours. "
                  "Serious incidents (injury, near-miss) must also be reported to the Safety Officer at "
                  "safety@company.com. All reports are confidential and used solely for improvement purposes.",
        "category": "Safety",
    },
]


def http_request(method: str, path: str, data=None, headers=None, files=None):
    url = f"{BASE_URL}{path}"
    if headers is None:
        headers = {}

    if files:
        # Multipart form-data (for file upload)
        import io
        boundary = "----FormBoundary7MA4YWxkTrZu0gW"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        body_parts = []
        for field_name, (filename, file_data, content_type) in files.items():
            body_parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; "
                f"filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n"
            )
        # We'll use requests-style below — but let's just use urllib with bytes
        body = b""
        for field_name, (filename, file_data, content_type) in files.items():
            body += f"--{boundary}\r\n".encode()
            body += f"Content-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"\r\n".encode()
            body += f"Content-Type: {content_type}\r\n\r\n".encode()
            body += file_data if isinstance(file_data, bytes) else file_data.encode()
            body += b"\r\n"
        body += f"--{boundary}--\r\n".encode()
    elif data is not None:
        if isinstance(data, dict) and headers.get("Content-Type") == "application/x-www-form-urlencoded":
            body = urllib.parse.urlencode(data).encode()
        else:
            body = json.dumps(data).encode()
            headers.setdefault("Content-Type", "application/json")
    else:
        body = None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def login():
    print("Logging in...")
    status, resp = http_request(
        "POST", "/auth/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if status != 200:
        print(f"  Login failed ({status}): {resp}")
        sys.exit(1)
    token = resp.get("access_token")
    print(f"  Login successful.")
    return token


def seed_faq(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\nSeeding {len(FAQ_ITEMS)} FAQ items into company {COMPANY_ID}...")

    # Get existing FAQs to avoid duplicates
    status, existing = http_request("GET", f"/faq/{COMPANY_ID}", headers=headers)
    existing_questions = {f["question"] for f in existing} if status == 200 else set()

    created = 0
    skipped = 0
    for item in FAQ_ITEMS:
        if item["question"] in existing_questions:
            print(f"  SKIP (exists): {item['question'][:60]}")
            skipped += 1
            continue

        status, resp = http_request(
            "POST", f"/faq/{COMPANY_ID}",
            data={**item, "is_published": True},
            headers=headers,
        )
        if status == 201:
            print(f"  CREATED: {item['question'][:60]}")
            created += 1
        else:
            print(f"  ERROR ({status}): {resp} | item: {item['question'][:40]}")

    print(f"  FAQ seed done: {created} created, {skipped} skipped.")


def seed_csv(token: str, filename: str, display_name: str):
    filepath = os.path.join(SAMPLES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    print(f"\nUploading CSV: {filename} as '{display_name}'...")

    with open(filepath, "rb") as f:
        file_data = f.read()

    boundary = "----AskAISeedBoundary"
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n".encode()
    body += b"Content-Type: text/csv\r\n\r\n"
    body += file_data
    body += b"\r\n"
    body += f"--{boundary}\r\n".encode()
    body += b"Content-Disposition: form-data; name=\"display_name\"\r\n\r\n"
    body += display_name.encode()
    body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    req = urllib.request.Request(
        f"{BASE_URL}/datasets/{COMPANY_ID}/upload-table",
        data=body,
        headers=upload_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            print(f"  UPLOADED: table='{result.get('table_name')}', rows={result.get('row_count')}")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read().decode())
        print(f"  ERROR ({e.code}): {err}")


if __name__ == "__main__":
    print("=" * 60)
    print("AskAI Sample Data Seeder")
    print("=" * 60)

    token = login()
    seed_faq(token)

    seed_csv(token, "monthly_sales.csv", "Monthly Sales Data")
    seed_csv(token, "employees.csv", "Employee Directory")
    seed_csv(token, "product_inventory.csv", "Product Inventory")

    print("\nDone! You can now chat with AskAI and ask questions like:")
    print("  - What is the leave policy?")
    print("  - Total profit in March 2024?")
    print("  - Which product has the highest stock?")
    print("  - Who is the Engineering Manager?")
    print("  - Total revenue in Q1 2024?")
