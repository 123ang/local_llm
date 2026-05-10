-- Clean analytical views for Kedah Investment Q&A
-- Purpose: avoid double-counting raw table grains and normalize 2025 RM values.
-- Re-runnable and non-destructive.

CREATE OR REPLACE VIEW kedah_clean_location_investment_employment AS
SELECT
  year,
  COALESCE(NULLIF(location, ''), breakdown_value) AS location,
  employment::integer AS employment,
  CASE
    -- 2025 source appears stored in RM while older rows are RM million.
    WHEN year = 2025 THEN total_rm_million / 1000000.0
    ELSE total_rm_million
  END AS investment_rm_million,
  projects,
  source_file,
  source_sheet,
  'location_breakdown; 2025 values normalized from RM to RM million; use this view for jobs concentration by area and overall trend ratio'::text AS methodology_note
FROM c2_approved_investment_llm_ready
WHERE total_rm_million IS NOT NULL
  AND employment IS NOT NULL
  AND (source_sheet ILIKE '%loc%' OR source_sheet ILIKE '%location%')
  AND COALESCE(NULLIF(location, ''), breakdown_value) IS NOT NULL;

CREATE OR REPLACE VIEW kedah_location_jobs_summary AS
SELECT
  location,
  SUM(employment)::integer AS total_employment,
  SUM(investment_rm_million) AS total_investment_rm_million,
  CASE
    WHEN SUM(investment_rm_million) > 0
    THEN SUM(employment) / (SUM(investment_rm_million) / 1000.0)
  END AS jobs_per_rm1b,
  COUNT(*) AS source_rows,
  MIN(year) AS first_year,
  MAX(year) AS latest_year
FROM kedah_clean_location_investment_employment
GROUP BY location;

CREATE OR REPLACE VIEW kedah_overall_jobs_per_rm1b_trend AS
SELECT
  SUM(employment)::integer AS total_employment,
  SUM(investment_rm_million) AS total_investment_rm_million,
  SUM(employment) / (SUM(investment_rm_million) / 1000.0) AS jobs_per_rm1b,
  MIN(year) AS first_year,
  MAX(year) AS latest_year,
  COUNT(*) AS source_rows,
  'Calculated from location-breakdown rows only to avoid double-counting state/country/industry copies of the same investment. 2025 values normalized from RM to RM million.'::text AS methodology_note
FROM kedah_clean_location_investment_employment;

CREATE OR REPLACE VIEW kedah_clean_sector_investment_employment AS
SELECT
  year,
  CASE
    WHEN COALESCE(NULLIF(industry, ''), breakdown_value) IN ('Paper,Printing & Publishing', 'Paper, Printing & Publishing') THEN 'Paper, Printing & Publishing'
    WHEN COALESCE(NULLIF(industry, ''), breakdown_value) IN ('Electrical & Electronics', 'Electronics & Electrical Products') THEN 'Electrical & Electronics'
    WHEN COALESCE(NULLIF(industry, ''), breakdown_value) IN ('Chemicals & Chemical Products', 'Chemical & Chemical Products') THEN 'Chemicals & Chemical Products'
    ELSE COALESCE(NULLIF(industry, ''), breakdown_value)
  END AS sector,
  employment::integer AS employment,
  CASE
    -- 2025 source appears stored in RM while older rows are RM million.
    WHEN year = 2025 THEN total_rm_million / 1000000.0
    ELSE total_rm_million
  END AS investment_rm_million,
  projects,
  source_file,
  source_sheet,
  CASE
    WHEN COALESCE(NULLIF(industry, ''), breakdown_value) IN ('Manufacturing', 'Services') THEN 'main_sector_or_total'
    ELSE 'industry_or_subsector'
  END AS category_level,
  'industry/sector breakdown; 2025 values normalized from RM to RM million; use this view for jobs per RM1b by sector'::text AS methodology_note
FROM c2_approved_investment_llm_ready
WHERE total_rm_million IS NOT NULL
  AND employment IS NOT NULL
  AND (breakdown_type = 'industry' OR source_sheet ILIKE '%ind%' OR source_sheet ILIKE '%industry%')
  AND COALESCE(NULLIF(industry, ''), breakdown_value) IS NOT NULL;

CREATE OR REPLACE VIEW kedah_sector_jobs_per_rm1b AS
SELECT
  sector,
  SUM(employment)::integer AS total_employment,
  SUM(investment_rm_million) AS total_investment_rm_million,
  CASE
    WHEN SUM(investment_rm_million) > 0
    THEN SUM(employment) / (SUM(investment_rm_million) / 1000.0)
  END AS jobs_per_rm1b,
  COUNT(*) AS source_rows,
  MIN(year) AS first_year,
  MAX(year) AS latest_year,
  STRING_AGG(DISTINCT category_level, ', ' ORDER BY category_level) AS category_levels,
  'Sector ratio = total_employment / (total_investment_rm_million / 1000). 2025 values normalized from RM to RM million.'::text AS methodology_note
FROM kedah_clean_sector_investment_employment
GROUP BY sector;
