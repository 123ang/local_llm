import os
import re
import zipfile
from pathlib import Path
from typing import List, Optional

import pandas as pd

# ============================================================
# CONFIG
# ============================================================
# Put your ZIP files here. You can add more ZIPs later.
SCRIPT_DIR = Path(__file__).parent
ZIP_INPUTS = [
    str(SCRIPT_DIR / "Approved Investment.zip"),
]

# Output folder
OUTPUT_DIR = str(SCRIPT_DIR / "output")
EXTRACT_DIR = os.path.join(OUTPUT_DIR, "extracted")

# Output CSVs
MASTER_CSV = os.path.join(OUTPUT_DIR, "approved_investment_master.csv")
LLM_READY_CSV = os.path.join(OUTPUT_DIR, "approved_investment_llm_ready.csv")
PROJECT_LIST_CSV = os.path.join(OUTPUT_DIR, "approved_investment_project_list.csv")

# Scope control
YEARLY_ONLY = True
KEEP_TOTAL_ROWS = False

# ============================================================
# HELPERS
# ============================================================
def ensure_dirs() -> None:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(EXTRACT_DIR).mkdir(parents=True, exist_ok=True)


def unzip_all(zip_paths: List[str], extract_root: str) -> None:
    for zip_path in zip_paths:
        if not os.path.exists(zip_path):
            print(f"[WARN] ZIP not found, skipped: {zip_path}")
            continue

        subfolder = Path(extract_root) / Path(zip_path).stem
        subfolder.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] Extracting: {zip_path}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(subfolder)


def extract_year(text: str) -> Optional[int]:
    match = re.search(r"(19|20)\d{2}", text)
    return int(match.group(0)) if match else None


def is_partial_year(text: str) -> bool:
    s = text.lower()
    patterns = [
        r"\bq[1-4]\b",
        r"jan\s*[-–]\s*mar",
        r"jan\s*[-–]\s*jun",
        r"jan\s*[-–]\s*sep",
        r"jan\s*[-–]\s*sept",
        r"apr\s*[-–]\s*jun",
        r"apr\s*[-–]\s*june",
        r"jan to",
        r"up to",
    ]
    return any(re.search(p, s) for p in patterns)


def infer_sector(file_path: str, sheet_name: str) -> str:
    s = f"{file_path} {sheet_name}".lower()
    if "manufact" in s or "mfg" in s:
        return "manufacturing"
    if "service" in s:
        return "services"
    if "various" in s or "economic sector" in s:
        return "various"
    return "unknown"


def infer_breakdown_type(file_path: str, sheet_name: str) -> str:
    s = f"{file_path} {sheet_name}".lower()
    if "by state" in s or re.search(r"\bstate\b", s):
        return "state"
    if "by ind" in s or "industry" in s:
        return "industry"
    if "by loc" in s or "location" in s or "factory location" in s:
        return "location"
    if "by country" in s or re.search(r"\bcountry\b", s):
        return "country"
    if "project listing" in s or "projects listing" in s or "list of companies" in s or "project list" in s:
        return "project_list"
    return "unknown"


def infer_geo_scope(file_path: str, sheet_name: str) -> str:
    s = f"{file_path} {sheet_name}".lower()
    if "kedah" in s:
        return "kedah_only"
    if "by state" in s or "malaysia" in s:
        return "malaysia_all_states"
    return "unknown"


def infer_data_grain(breakdown_type: str, period_type: str) -> str:
    if period_type == "year":
        return f"annual_{breakdown_type}"
    return f"unknown_{breakdown_type}"


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def looks_like_total(text: str) -> bool:
    s = text.strip().lower()
    total_terms = {
        "total", "grand total", "jumlah", "jumlah besar", "sum", "overall total"
    }
    return s in total_terms


def find_header_row(raw_df: pd.DataFrame) -> int:
    keywords = [
        "project", "projects", "employment", "employement", "invest", "domestic", "foreign",
        "state", "industry", "country", "location", "million", "rm"
    ]

    max_rows = min(30, len(raw_df))
    best_row = 0
    best_score = 0
    
    for i in range(max_rows):
        row = raw_df.iloc[i].astype(str).str.lower().fillna("")
        joined = " | ".join(row.tolist())
        
        # Count keyword matches
        score = sum(1 for k in keywords if k in joined)
        
        # Bonus: if row has multiple non-empty values (likely a header row, not a title)
        non_empty_count = sum(1 for v in row if v and v != "nan" and len(str(v).strip()) > 0)
        
        # Prefer rows with more non-empty cells (actual headers have multiple columns)
        if non_empty_count >= 3:
            score += 2
        
        # Penalize rows that look like titles (very long single cell or mostly empty)
        if non_empty_count == 1 and len(str(row.iloc[0])) > 50:
            score -= 3
        
        if score > best_score:
            best_score = score
            best_row = i
    
    # If we found a good header row, return it; otherwise default to 0
    return best_row if best_score >= 2 else 0


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}

    for col in df.columns:
        c = normalize_text(col).lower()

        # Breakdown value columns
        if c in {"state", "industry", "country", "location"} or any(x in c for x in ["state", "industry", "country", "location"]):
            # Only rename if it's clearly a breakdown column (not if it's part of another word)
            if c in {"state", "industry", "country", "location"} or \
               any(c.startswith(x + " ") or c.endswith(" " + x) or (" " + x + " ") in c for x in ["state", "industry", "country", "location"]):
                rename_map[col] = "breakdown_value"
        # Projects columns - more flexible matching
        elif "project" in c and ("no" in c or "number" in c or c == "projects"):
            rename_map[col] = "projects"
        # Employment columns - handle typos like "employement"
        elif "employ" in c:
            rename_map[col] = "employment"
        # Investment columns
        elif "domestic" in c and ("invest" in c or "rm" in c or "million" in c):
            rename_map[col] = "domestic_rm_million"
        elif "foreign" in c and ("invest" in c or "rm" in c or "million" in c):
            rename_map[col] = "foreign_rm_million"
        elif "total" in c and "invest" in c and ("rm" in c or "million" in c):
            rename_map[col] = "total_rm_million"

    df = df.rename(columns=rename_map)

    # Try to find breakdown_value if not found - check first column
    if "breakdown_value" not in df.columns and len(df.columns) > 0:
        first_col = df.columns[0]
        first_col_lower = normalize_text(first_col).lower()
        # If first column looks like a breakdown column, use it
        if any(x in first_col_lower for x in ["state", "industry", "country", "location", "district", "area"]):
            df = df.rename(columns={first_col: "breakdown_value"})

    expected = [
        "breakdown_value",
        "projects",
        "employment",
        "domestic_rm_million",
        "foreign_rm_million",
        "total_rm_million",
    ]

    for col in expected:
        if col not in df.columns:
            df[col] = None

    # Only select expected columns if they exist
    available_cols = [col for col in expected if col in df.columns]
    if "breakdown_value" not in available_cols:
        # If no breakdown_value, we can't process this sheet
        return pd.DataFrame()
    
    df = df[available_cols].copy()

    if "breakdown_value" in df.columns:
        df["breakdown_value"] = df["breakdown_value"].apply(normalize_text)

    for col in ["projects", "employment", "domestic_rm_million", "foreign_rm_million", "total_rm_million"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def populate_dimension_columns(df: pd.DataFrame, breakdown_type: str, geo_scope: str) -> pd.DataFrame:
    df["state"] = None
    df["industry"] = None
    df["country"] = None
    df["location"] = None

    if breakdown_type == "state":
        df["state"] = df["breakdown_value"]
    elif breakdown_type == "industry":
        df["industry"] = df["breakdown_value"]
        if geo_scope == "kedah_only":
            df["state"] = "Kedah"
    elif breakdown_type == "country":
        df["country"] = df["breakdown_value"]
        if geo_scope == "kedah_only":
            df["state"] = "Kedah"
    elif breakdown_type == "location":
        df["location"] = df["breakdown_value"]
        if geo_scope == "kedah_only":
            df["state"] = "Kedah"

    return df


def clean_rows(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["breakdown_value"].notna()].copy()
    df = df[df["breakdown_value"].astype(str).str.strip() != ""].copy()

    if not KEEP_TOTAL_ROWS:
        df = df[~df["breakdown_value"].apply(looks_like_total)].copy()

    # remove rows that are entirely empty numerically
    numeric_cols = ["projects", "employment", "domestic_rm_million", "foreign_rm_million", "total_rm_million"]
    df = df[df[numeric_cols].notna().any(axis=1)].copy()

    return df


def read_sheet(file_path: str, sheet_name: str) -> pd.DataFrame:
    raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    header_row = find_header_row(raw)
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
    return df


def process_summary_sheet(file_path: str, sheet_name: str) -> Optional[pd.DataFrame]:
    combined_text = f"{file_path} {sheet_name}"
    year = extract_year(combined_text)
    if year is None:
        return None

    partial = is_partial_year(combined_text)
    if YEARLY_ONLY and partial:
        return None

    period_type = "year"
    sector = infer_sector(file_path, sheet_name)
    breakdown_type = infer_breakdown_type(file_path, sheet_name)
    geo_scope = infer_geo_scope(file_path, sheet_name)

    if breakdown_type == "project_list":
        return None

    df = read_sheet(file_path, sheet_name)
    df = standardize_columns(df)
    df = clean_rows(df)
    if df.empty:
        return None

    df = populate_dimension_columns(df, breakdown_type, geo_scope)

    df["year"] = year
    df["period_type"] = period_type
    df["is_partial_year"] = partial
    df["geo_scope"] = geo_scope
    df["sector"] = sector
    df["breakdown_type"] = breakdown_type
    df["data_grain"] = infer_data_grain(breakdown_type, period_type)
    df["source_file"] = Path(file_path).name
    df["source_sheet"] = sheet_name

    output_cols = [
        "year",
        "period_type",
        "is_partial_year",
        "geo_scope",
        "sector",
        "breakdown_type",
        "breakdown_value",
        "state",
        "industry",
        "country",
        "location",
        "projects",
        "employment",
        "domestic_rm_million",
        "foreign_rm_million",
        "total_rm_million",
        "data_grain",
        "source_file",
        "source_sheet",
    ]
    return df[output_cols].copy()


def process_project_list_sheet(file_path: str, sheet_name: str) -> Optional[pd.DataFrame]:
    combined_text = f"{file_path} {sheet_name}"
    if infer_breakdown_type(file_path, sheet_name) != "project_list":
        return None

    year = extract_year(combined_text)
    period_type = "year"
    partial = is_partial_year(combined_text)
    if YEARLY_ONLY and partial:
        return None

    try:
        df = read_sheet(file_path, sheet_name)
    except Exception:
        return None

    df.columns = [normalize_text(c) for c in df.columns]
    df = df.dropna(how="all").copy()
    if df.empty:
        return None

    df["year"] = year
    df["period_type"] = period_type
    df["is_partial_year"] = partial
    df["source_file"] = Path(file_path).name
    df["source_sheet"] = sheet_name
    return df


def build_csvs() -> None:
    ensure_dirs()
    unzip_all(ZIP_INPUTS, EXTRACT_DIR)

    excel_files = list(Path(EXTRACT_DIR).rglob("*.xlsx")) + list(Path(EXTRACT_DIR).rglob("*.xls"))

    summary_frames = []
    project_frames = []

    print(f"[INFO] Excel files found: {len(excel_files)}")

    for file_path in excel_files:
        print(f"[INFO] Processing file: {file_path.name}")
        try:
            xls = pd.ExcelFile(file_path)
        except Exception as e:
            print(f"[WARN] Could not open {file_path.name}: {e}")
            continue

        for sheet_name in xls.sheet_names:
            try:
                summary_df = process_summary_sheet(str(file_path), sheet_name)
                if summary_df is not None and not summary_df.empty:
                    summary_frames.append(summary_df)

                project_df = process_project_list_sheet(str(file_path), sheet_name)
                if project_df is not None and not project_df.empty:
                    project_frames.append(project_df)
            except Exception as e:
                print(f"[WARN] Failed sheet {sheet_name} in {file_path.name}: {e}")

    if summary_frames:
        master_df = pd.concat(summary_frames, ignore_index=True)
        master_df.to_csv(MASTER_CSV, index=False)

        llm_ready_df = master_df.copy()
        llm_ready_df = llm_ready_df.sort_values(
            by=["year", "sector", "breakdown_type", "breakdown_value"],
            na_position="last"
        ).reset_index(drop=True)
        llm_ready_df.to_csv(LLM_READY_CSV, index=False)

        print(f"[OK] Master CSV written: {MASTER_CSV}")
        print(f"[OK] LLM-ready CSV written: {LLM_READY_CSV}")
        print(f"[OK] Rows in LLM-ready CSV: {len(llm_ready_df)}")
    else:
        print("[WARN] No summary data found.")

    if project_frames:
        project_list_df = pd.concat(project_frames, ignore_index=True)
        project_list_df.to_csv(PROJECT_LIST_CSV, index=False)
        print(f"[OK] Project list CSV written: {PROJECT_LIST_CSV}")
        print(f"[OK] Rows in project list CSV: {len(project_list_df)}")
    else:
        print("[INFO] No project list sheets found.")


if __name__ == "__main__":
    build_csvs()
