# Approved Investment → LLM-Ready CSV → PostgreSQL → Dashboard Guide

## Goal
Build a clean workflow for your Approved Investment files so you can:

1. unzip and clean the source files
2. generate an **LLM-ready CSV**
3. optionally load that CSV into **PostgreSQL**
4. connect it to a dashboard
5. ask useful questions with an LLM safely and consistently

---

## Recommended final outputs
Prepare these 3 files:

### 1. `approved_investment_master.csv`
This is the raw-cleaned combined dataset.
Use it for checking whether extraction worked correctly.

### 2. `approved_investment_llm_ready.csv`
This is the most important file.
Use it for:
- PostgreSQL import
- LLM querying
- dashboard connection

### 3. `approved_investment_project_list.csv` *(optional)*
Use this only if some sheets contain company/project-level listings.
Keep it separate from the summary dataset.

---

## Best structure for the LLM-ready CSV
Use **one row = one fact**.

Recommended columns:

| Column | Meaning |
|---|---|
| `year` | reporting year |
| `period_type` | always `year` |
| `is_partial_year` | `false` for full-year rows |
| `geo_scope` | e.g. `kedah_only` or `malaysia_all_states` |
| `sector` | `manufacturing`, `services`, `various`, `unknown` |
| `breakdown_type` | `state`, `industry`, `country`, `location` |
| `breakdown_value` | the main value for the breakdown |
| `state` | explicit state name if known |
| `industry` | explicit industry name if known |
| `country` | explicit country name if known |
| `location` | explicit district/location if known |
| `projects` | number of projects |
| `employment` | number of jobs/employment |
| `domestic_rm_million` | domestic investment in RM million |
| `foreign_rm_million` | foreign investment in RM million |
| `total_rm_million` | total investment in RM million |
| `data_grain` | e.g. `annual_state`, `annual_industry`, `annual_country`, `annual_location` |
| `source_file` | source filename |
| `source_sheet` | source sheet name |

This structure is good because the LLM can answer questions without guessing joins.

---

## Why this is LLM-friendly
This format helps the model answer directly:

- Which year had the highest total approved investment?
- Which country invested the most in Kedah?
- Which location had the most projects?
- Compare domestic vs foreign investment by year.
- Which industry created the most jobs?

Because the values are already flattened into explicit columns, the model does not need to infer hidden relationships.

---

## Workflow: what to do step by step

## Step 1 — Organize your source files
Put all ZIPs or extracted Excel files into one folder.

Recommended structure:

```text
approved_investment/
  raw_zip/
    Approved Investment 2020.zip
    Approved Investment 2022.zip
  extracted/
  output/
  scripts/
```

---

## Step 2 — Build the CSV first, not the database
Do **not** load messy Excel files directly into PostgreSQL.

Better flow:

```text
ZIP / Excel / PDF
    ↓
cleaning script
    ↓
LLM-ready CSV
    ↓
PostgreSQL
    ↓
LLM + Dashboard
```

This makes debugging much easier.

---

## Step 3 — Rules for cleaning
Your files vary by year and sheet, so use these rules.

### A. Header row detection
Some sheets have titles above the real table.
So:
- read the sheet with `header=None`
- inspect the first 20–30 rows
- find the row containing keywords like:
  - `projects`
  - `investment`
  - `employment`
  - `state`
  - `industry`
  - `country`
  - `location`

### B. Standardize column names
Map different source names into one standard naming system.

Examples:
- `No. of Projects` → `projects`
- `No.of Projects` → `projects`
- `Employment` → `employment`
- `Total Employment` → `employment`
- `Domestic Investment` → `domestic_rm_million`
- `Foreign Investment` → `foreign_rm_million`
- `Total Investment` → `total_rm_million`
- `State` / `Industry` / `Country` / `Location` → `breakdown_value`

### C. Standardize text values
Convert sector names into only these:
- `manufacturing`
- `services`
- `various`
- `unknown`

Convert breakdown types into only these:
- `state`
- `industry`
- `country`
- `location`
- `unknown`

### D. Remove noisy rows
Drop rows like:
- `Total`
- `Grand Total`
- blank rows
- repeated title rows
- note rows / footnotes

### E. Keep unit consistency
Store all money columns in **RM million** if that is the dominant format.
If a file uses RM instead of RM million, convert it before export.

---

## Step 4 — Populate explicit dimension columns
Do not only keep `breakdown_value`.
Also fill the matching dimension column.

### Example
If a row is from a `By Country` sheet:
- `breakdown_type = country`
- `breakdown_value = Japan`
- `country = Japan`
- `state = Kedah` if the file is Kedah-only

If a row is from a `By Industry` sheet:
- `breakdown_type = industry`
- `breakdown_value = Food Manufacturing`
- `industry = Food Manufacturing`
- `state = Kedah` if known

This makes the CSV much easier for LLMs and dashboards.

---

## Step 5 — Export two CSVs

### `approved_investment_master.csv`
This can be broader and closer to the source.
Use it for validation.

### `approved_investment_llm_ready.csv`
This should be:
- cleaned
- standardized
- flat
- explicit
- yearly only if that is your chosen scope

---

## Step 6 — Import CSV into PostgreSQL
After your LLM-ready CSV is correct, create a table like this:

```sql
CREATE TABLE approved_investment_llm_ready (
  id BIGSERIAL PRIMARY KEY,
  year INT,
  period_type TEXT,
  is_partial_year BOOLEAN,
  geo_scope TEXT,
  sector TEXT,
  breakdown_type TEXT,
  breakdown_value TEXT,
  state TEXT,
  industry TEXT,
  country TEXT,
  location TEXT,
  projects INT,
  employment INT,
  domestic_rm_million NUMERIC,
  foreign_rm_million NUMERIC,
  total_rm_million NUMERIC,
  data_grain TEXT,
  source_file TEXT,
  source_sheet TEXT
);
```

Then load with:

```sql
COPY approved_investment_llm_ready (
  year, period_type, is_partial_year, geo_scope, sector,
  breakdown_type, breakdown_value, state, industry, country, location,
  projects, employment, domestic_rm_million, foreign_rm_million, total_rm_million,
  data_grain, source_file, source_sheet
)
FROM '/absolute/path/approved_investment_llm_ready.csv'
DELIMITER ','
CSV HEADER;
```

---

## Step 7 — Create a simple query view for the LLM
Create a view so the LLM only queries a safe surface.

```sql
CREATE OR REPLACE VIEW v_approved_investment AS
SELECT
  year,
  period_type,
  geo_scope,
  sector,
  breakdown_type,
  breakdown_value,
  state,
  industry,
  country,
  location,
  projects,
  employment,
  domestic_rm_million,
  foreign_rm_million,
  total_rm_million,
  data_grain
FROM approved_investment_llm_ready;
```

This keeps the chatbot simple.

---

## Step 8 — What code you should write
Create these scripts.

### 1. `build_llm_ready_csv.py`
Purpose:
- unzip files
- read Excel sheets
- detect header rows
- clean columns
- infer metadata
- export the CSVs

### 2. `load_csv_to_postgres.py`
Purpose:
- connect to PostgreSQL
- create table if needed
- load the final CSV
- create the view

### 3. `ask_db.py` *(optional later)*
Purpose:
- send a user question to an LLM
- let it generate SQL against the view
- run the SQL
- return the result safely

---

## Suggested Python logic for `build_llm_ready_csv.py`

### Main flow
1. unzip all ZIP files
2. scan for `.xlsx` and `.xls`
3. read each sheet raw
4. detect header row
5. read again with the correct header
6. standardize columns
7. infer:
   - `year`
   - `sector`
   - `breakdown_type`
   - `geo_scope`
   - `data_grain`
8. populate explicit fields:
   - `state`
   - `industry`
   - `country`
   - `location`
9. remove noisy rows
10. export CSV

---

## Minimum libraries to install

```bash
pip install pandas openpyxl xlrd
```

If you later load to PostgreSQL:

```bash
pip install sqlalchemy psycopg2-binary
```

---

## Example quality checks before using the CSV
Open the final CSV and verify:

1. `year` is always filled
2. `sector` only contains allowed values
3. `breakdown_type` only contains allowed values
4. `projects`, `employment`, `domestic`, `foreign`, `total` are numeric
5. no obvious duplicate totals unless intentionally kept
6. no title rows remain
7. no mixed units remain

---

## Best questions you can ask the LLM

## Trend questions
- Which year had the highest total approved investment in Kedah?
- How did total approved investment change from 2020 to 2025?
- Which year had the highest number of projects?
- Which year created the most employment?

## Sector questions
- Compare manufacturing and services by year.
- Which sector contributed the most total investment?
- Which sector created the most jobs?

## Industry questions
- Which industries attracted the highest investment in Kedah?
- Which industry had the highest foreign investment?
- Which industries created the most employment?
- Show the top 10 industries by total investment.

## Country questions
- Which countries invested the most in Kedah?
- Which country had the highest foreign investment in 2022?
- Show the top 10 source countries by foreign investment.

## Location questions
- Which locations in Kedah had the most projects?
- Which location had the highest total investment?
- Which location created the most employment?

## Comparison questions
- Compare domestic vs foreign investment by year.
- Which years depended more on foreign investment than domestic investment?
- Compare project counts and employment by industry.

## Ranking questions
- Top 5 years by total investment
- Top 10 industries by employment
- Top 10 countries by foreign investment
- Top 10 locations by project count

## Insight questions
- Is Kedah more dependent on foreign or domestic investment?
- Do years with more projects always create more employment?
- Which industries appear to drive investment most strongly?

---

## Questions to avoid unless your data supports them
Avoid asking these unless you clearly include the fields:

- monthly trends
- day-level approval dates
- company-level questions from summary tables
- quarter comparisons if you removed quarterly rows
- exact district-to-state hierarchy if not explicitly stored

---

## Best LLM prompt strategy
When you connect an LLM to the CSV or PostgreSQL view, always tell it:

1. what the table/view name is
2. what each important column means
3. that all money is in RM million
4. that it should query only the approved view
5. that it must never invent columns

### Example system instruction

```text
You are querying a PostgreSQL view named v_approved_investment.
Use only columns that exist in this view.
All investment amounts are stored in RM million.
Do not invent columns.
Prefer simple aggregate SQL with GROUP BY and ORDER BY.
```

---

## Recommended roadmap for you

### Phase 1
- finalize yearly-only scope
- build `approved_investment_llm_ready.csv`
- validate 20–50 rows manually

### Phase 2
- import CSV into PostgreSQL
- create `v_approved_investment`
- test manual SQL queries

### Phase 3
- connect an LLM to the PostgreSQL view
- allow safe read-only SQL generation
- add charts/dashboard on top

### Phase 4
- add glossary metadata
- add project-list dataset separately
- add quarterly data later if needed

---

## Final recommendation
For your use case, the best setup is:

```text
Source Excel/ZIP
→ build_llm_ready_csv.py
→ approved_investment_llm_ready.csv
→ PostgreSQL table
→ v_approved_investment
→ LLM + Dashboard
```

This is the cleanest and safest path.

---

## Extra note
You already have a starter builder script. The next best improvement is to create a **version 2 builder** that also:

- separates yearly and quarterly cleanly
- creates `project_list.csv`
- adds `geo_scope`
- adds `data_grain`
- removes total rows more safely
- standardizes more sector names

That would make your dataset much stronger for both analytics and LLM usage.

