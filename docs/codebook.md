# Codebook

Variables in `data/processed/` (built by `python -m idsp.data.panel`). Percentages are on a
0-100 scale. Baseline variables use the latest non-missing value in 2010-2014.

## Keys and treatment

| Variable | Description |
|---|---|
| `iso3` | ISO 3166-1 alpha-3 code (synthetic data use codes starting with "S") |
| `year` / `wave` | Calendar year (2014-2024) / Findex wave (2014, 2017, 2021, 2024) |
| `region`, `income_group` | World Bank region and FY2015 income group (L, LM, UM) |
| `rollout_year` | Start of nationwide enrolment in a digital foundational ID (coding protocol, section 3) |
| `rollout_year_alt` | Year the establishing legal instrument entered into force |
| `cohort_annual` | First treated year for annual outcomes = `rollout_year` + lag (lag 0) |
| `cohort_wave` | First treated Findex wave: first wave w with `rollout_year` + 1 <= w |
| `biometric_enrolment`, `biometric_auth_mandatory_benefits`, `non_biometric_fallback`, `linked_social_registry`, `donor_financed` | Design features at rollout (0/1/blank) |

## Outcomes

| Variable | Description | Source |
|---|---|---|
| `sdg131_total` | Population covered by at least one social protection benefit, % (SDG 1.3.1) | ILO WSPD / ILOSTAT |
| `transfer_total` | Adults (15+) who received a government transfer or government pension in the past 12 months, % | Global Findex |
| `transfer_female`, `transfer_male` | Same, by sex | Global Findex |
| `transfer_poor40`, `transfer_rich60` | Same, poorest 40% / richest 60% of households by income within the country | Global Findex |
| `transfer_rural`, `transfer_urban` | Same, by residence (availability to be verified per wave) | Global Findex |
| `gap_sex` | `transfer_male` - `transfer_female` (percentage points) | derived |
| `gap_income` | `transfer_rich60` - `transfer_poor40` | derived |
| `gap_residence` | `transfer_urban` - `transfer_rural` | derived |
| `elec_access` | Access to electricity, % of population (placebo) | WDI EG.ELC.ACCS.ZS |
| `agri_land` | Agricultural land, % of land area (placebo) | WDI AG.LND.AGRI.ZS |

Construction of `transfer_total` must use one definition across the four waves. Record here the
Findex item codes used for each wave before the first real run:

| Wave | Item(s) | Note |
|---|---|---|
| 2014 | VERIFY | |
| 2017 | VERIFY | |
| 2021 | VERIFY | Check whether COVID-related payments can be separated |
| 2024 | VERIFY | |

## Baseline covariates and moderators

| Variable | Description | Source |
|---|---|---|
| `log_gdppc_2014` | log GDP per capita, PPP, constant international $ | WDI NY.GDP.PCAP.PP.KD |
| `urban_2014` | Urban population, % of total | WDI SP.URB.TOTL.IN.ZS |
| `mobile_2014` | Mobile cellular subscriptions per 100 people | WDI IT.CEL.SETS.P2 |
| `conflict_2010_2014` | 1 if battle-related deaths >= 25 in any year 2010-2014 | WDI VC.BTL.DETH (UCDP) |
| `sp_spending_2014` | Public social protection expenditure excluding health, % of GDP | ILO WSPD |
| `wgi_va_2014`, `wgi_rl_2014` | WGI Voice and Accountability; Rule of Law (estimate) | WGI |
| `vdem_cspart_2014` | V-Dem civil society participation index (`v2x_cspart`) | V-Dem |
| `dp_law_year` | Year a comprehensive data protection law entered into force | hand-coded |
| `dp_law_in_force` | 1 if `dp_law_year` <= 2014 | derived |
| `safeguard` | Mean of z-scores of `wgi_va_2014`, `wgi_rl_2014`, `vdem_cspart_2014`, `dp_law_in_force` | derived |
| `high_safeguard` | 1 if `safeguard` is above the sample median | derived |
