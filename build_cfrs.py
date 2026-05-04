import pandas as pd
import numpy as np

# ── 1. Load raw IDEA export ──────────────────────────────────────────────────
df_raw = pd.read_csv('/home/claude/export_table.csv', encoding='utf-8',
                     on_bad_lines='skip', header=None)

headers = df_raw.iloc[1].tolist()
data    = df_raw.iloc[2:].copy()
data.columns = headers
data    = data.reset_index(drop=True)

# ── 2. Select & rename the 12 CFRS columns ──────────────────────────────────
col_map = {
    headers[0]:  'Country',
    headers[1]:  'ISO2',
    headers[2]:  'ISO3',
    # Pillar A – Prohibitions
    headers[3]:  'A1_foreign_ban',        # Q1  foreign donations banned
    headers[9]:  'A2_anon_ban',           # Q7  anonymous donations banned
    headers[5]:  'A3_corporate_ban',      # Q3  corporate donations banned
    headers[29]: 'A4_banking_required',   # Q27 cash limited (banking system)
    # Pillar B – Spending limits
    headers[43]: 'B1_cand_spend_limit',   # Q41 candidate spending limit
    headers[41]: 'B2_party_spend_limit',  # Q39 party spending limit
    # Pillar C – Transparency
    headers[54]: 'C1_donor_disclosure',   # Q52 donor identity disclosed
    headers[56]: 'C2_exp_disclosure',     # Q54 itemized expenditure disclosed
    headers[50]: 'C3_pre_election_rep',   # Q48 election campaign reporting
    headers[49]: 'C4_regular_reporting',  # Q47 regular (post-election) reporting
    # Pillar D – Enforcement
    headers[58]: 'D1_oversight_body',     # Q56 responsible institution
    headers[60]: 'D2_sanctions',          # Q58 sanctions for violations
}

df = data.rename(columns=col_map)[list(col_map.values())].copy()

# ── 3. Scoring functions ─────────────────────────────────────────────────────

def score_yesno(val):
    """Standard Yes/No scorer."""
    v = str(val).strip()
    if v in ('Yes',):                        return 1.0
    if v in ('Yes, above certain threshold', 'Sometimes'): return 0.5
    if v in ('No', 'Not applicable', 'nan'): return 0.0
    if v == 'No data':                       return np.nan
    # Default: if starts with Yes, partial
    if v.lower().startswith('yes'):          return 0.5
    return 0.0

def score_oversight(val):
    """D1: independent oversight body."""
    v = str(val).strip()
    if v == 'No data':                       return np.nan
    if v == 'No institution specified':      return 0.0
    # Truly independent specialised body
    if 'Special agency for political finance' in v: return 1.0
    # Court or EMB – somewhat independent
    if any(x in v for x in ('EMB', 'Court', 'Auditing agency')): return 0.5
    # Ministry only – not independent
    if v == 'Ministry Auditing agency':      return 0.5
    return 0.0

def score_sanctions(val):
    """D2: quality/severity of sanctions."""
    v = str(val).strip()
    if v in ('Not applicable', 'nan', ''):   return 0.0
    # Strong: includes prison or deregistration or loss of office
    strong = any(x in v for x in ('Prison', 'Deregistration', 'Loss of elected office'))
    if strong:                               return 1.0
    # Weak: only fines or loss of public funding
    if 'Fines' in v or 'Loss of public funding' in v: return 0.5
    return 0.0

# ── 4. Apply scoring ─────────────────────────────────────────────────────────
score_cols = {
    'A1_foreign_ban':     score_yesno,
    'A2_anon_ban':        score_yesno,
    'A3_corporate_ban':   score_yesno,
    'A4_banking_required':score_yesno,
    'B1_cand_spend_limit':score_yesno,
    'B2_party_spend_limit':score_yesno,
    'C1_donor_disclosure':score_yesno,
    'C2_exp_disclosure':  score_yesno,
    'C3_pre_election_rep':score_yesno,
    'C4_regular_reporting':score_yesno,
    'D1_oversight_body':  score_oversight,
    'D2_sanctions':       score_sanctions,
}

VARS = list(score_cols.keys())
for col, fn in score_cols.items():
    df[f's_{col}'] = df[col].apply(fn)

score_var_cols = [f's_{c}' for c in VARS]

# ── 5. Compute CFRS ──────────────────────────────────────────────────────────
# Fill NaN with 0 (no data treated as absence of rule – conservative approach)
df[score_var_cols] = df[score_var_cols].fillna(0)
df['CFRS']        = df[score_var_cols].sum(axis=1) / 12
df['CFRS_scaled'] = (df['CFRS'] * 100).round(2)

# ── 6. Save processed file ───────────────────────────────────────────────────
out_cols = ['Country', 'ISO2', 'ISO3'] + score_var_cols + ['CFRS', 'CFRS_scaled']
df_out = df[out_cols].copy()
df_out.to_csv('/home/claude/cfrs_scores.csv', index=False)

# ── 7. Preview results ───────────────────────────────────────────────────────
display = df[['Country', 'CFRS_scaled'] + score_var_cols].sort_values('CFRS_scaled', ascending=False)
display.columns = ['Country','CFRS(0-100)'] + [c.replace('s_','') for c in score_var_cols]
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 120)
print(display.to_string(index=False))
print(f"\nSaved to /home/claude/cfrs_scores.csv")
