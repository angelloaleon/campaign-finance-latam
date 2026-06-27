-- ============================================================
-- Campaign Finance Regulatory Score (CFRS) — SQL analysis
-- Database: SQLite. Tables loaded from the project CSVs by load_db.py
--   cfrs    : per-country CFRS scores (32 countries)
--   cpi     : Transparency International CPI 2025 (AME region)
-- ============================================================


-- Query 1 ----------------------------------------------------
-- The analysis set: join CFRS to CPI on ISO3 country code.
-- This is the SQL equivalent of the pandas merge in the notebook.
-- Returns the 30 countries that have BOTH a CFRS and a CPI score.
SELECT
    c.Country,
    c.CFRS_scaled        AS cfrs,
    p.cpi_2025           AS cpi
FROM cfrs AS c
INNER JOIN cpi AS p
    ON c.ISO3 = p.ISO3
ORDER BY c.CFRS_scaled DESC;


-- Query 2 ----------------------------------------------------
-- Tiered ranking: bucket countries into regulatory-strength tiers
-- using CASE, then order strongest to weakest.
SELECT
    Country,
    CFRS_scaled AS cfrs,
    CASE
        WHEN CFRS_scaled >= 83 THEN 'Strong framework'
        WHEN CFRS_scaled >= 62 THEN 'Partial framework'
        ELSE 'Weak / no framework'
    END AS tier
FROM cfrs
ORDER BY CFRS_scaled DESC;


-- Query 3 ----------------------------------------------------
-- Regional pillar averages: how strong is each of the 4 pillars
-- on average across all 32 countries? Built from the variable-level
-- scores. Shows where the region is strongest and weakest.
SELECT 'A — Prohibitions'   AS pillar,
       ROUND(AVG((s_A1_foreign_ban + s_A2_anon_ban
                + s_A3_corporate_ban + s_A4_banking_required) / 4.0) * 100, 1) AS avg_score
FROM cfrs
UNION ALL
SELECT 'B — Spending Limits',
       ROUND(AVG((s_B1_cand_spend_limit + s_B2_party_spend_limit) / 2.0) * 100, 1)
FROM cfrs
UNION ALL
SELECT 'C — Transparency',
       ROUND(AVG((s_C1_donor_disclosure + s_C2_exp_disclosure
                + s_C3_pre_election_rep + s_C4_regular_reporting) / 4.0) * 100, 1)
FROM cfrs
UNION ALL
SELECT 'D — Enforcement',
       ROUND(AVG((s_D1_oversight_body + s_D2_sanctions) / 2.0) * 100, 1)
FROM cfrs
ORDER BY avg_score DESC;
