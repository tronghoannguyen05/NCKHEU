# Coding protocol: digital ID rollout dataset

This protocol governs `data/rollout/rollout_coding.csv` (one reconciled row per country),
`data/rollout/rollout_second_coder.csv` (independent second coding of a 20% sample) and
`data/rollout/dp_law_coding.csv` (data protection law in force). The rollout dataset is the
project's original contribution and will be released openly, so every coded value must be
traceable to its sources.

## 1. Blinding

Coders must not open outcome data (SDG 1.3.1, Findex) or any estimation output while coding.
The coding is frozen with the git tag `coding-freeze` before outcomes are merged with rollout
dates. Any later correction is logged in `docs/deviations.md` with the reason and the date.

## 2. What counts as a digital foundational ID

A country is coded as having a digital foundational ID when all three conditions hold:

1. **Foundational.** The system provides general-purpose legal identity for the resident or
   citizen population and is run by a civil registration or identification authority. Functional
   systems built for one purpose (voter registers, tax numbers, health cards, programme-specific
   beneficiary IDs such as a social registry card) do not count.
2. **Digital.** At least one of: (a) biometrics are captured into a central database used for
   deduplication; (b) the credential carries a chip or a digitally signed machine-readable
   element; (c) identity can be authenticated online against a central database.
3. **National.** Enrolment is open to the general public nationwide. Pilots limited to some
   provinces or to particular groups (for example civil servants) do not count.

## 3. Rollout year

- `rollout_year`: the first calendar year in which condition 3 was met, that is, the start of
  nationwide public enrolment in a system meeting conditions 1 and 2.
- If a country had a digital foundational system before a newer one, code the **first** system
  (treatment is absorbing). Record later upgrades in `notes` with years.
- If the country had no digital foundational ID by the end of 2024, write `rollout_event = none`
  and leave `rollout_year` blank.
- `rollout_year_alt`: the year the legal instrument establishing the system entered into force.
  Used only in robustness check R5.
- `rollout_event`: short description of the event dated (for example "nationwide enrolment
  opened", "first cards issued nationwide").
- `confidence`: `high` (two primary sources agree on the year), `medium` (sources agree within one
  year or only one primary source), `low` (conflicting sources; explain in `notes`).

## 4. Design features (coded at rollout)

| Field | 1 means | Blank means |
|---|---|---|
| `biometric_enrolment` | Biometrics captured at enrolment | Not established |
| `biometric_auth_mandatory_benefits` | Biometric authentication is required to receive at least one national cash transfer or pension | Not established |
| `non_biometric_fallback` | A non-biometric alternative (OTP, nominee, manual override) is legally provided for benefit receipt | Not established |
| `linked_social_registry` | The ID number is a required key of the national social registry | Not established |
| `donor_financed` | A donor-financed project (for example a World Bank IPF with an ID component) financed enrolment | Not established |

Use 0 only when a source establishes the absence of the feature. Do not infer 0 from silence.

## 5. Sources

Hierarchy, from most to least authoritative:

1. legislation, decrees, official gazettes;
2. reports and statistics of the ID authority or the ministry in charge;
3. World Bank ID4D country diagnostics and project documents;
4. reports of international organisations (UNHCR, UNICEF, UNDP, GSMA);
5. reputable news archives.

A `final` row needs **two independent sources** (different organisations), at least one from
levels 1-3. Record the full citation, the URL and the access date for each. Save a PDF or an
archived copy (for example web.archive.org) for every source in a private folder; record its
file name in `notes` if the URL may disappear.

## 6. Data protection law (`dp_law_coding.csv`)

- `dp_law_year`: the year a **comprehensive** personal data protection law entered into force.
  Sectoral provisions (banking secrecy, telecoms) do not count. A constitutional right to
  privacy alone does not count.
- Status can be checked against the UNCTAD Data Protection and Privacy Legislation Worldwide
  tracker, which records current status but not the year; the year must come from the law itself.

## 7. Double coding and agreement

1. Draw the sample: `python -m idsp.coding sample` (20% of countries, fixed seed).
2. The second coder codes these countries independently in `rollout_second_coder.csv`, using
   this protocol only.
3. Compute agreement: `python -m idsp.coding agreement`. The output reports agreement on
   having a digital ID, exact-year agreement, agreement within one year, the mean absolute
   difference, and Cohen's kappa for each design feature.
4. If exact-year agreement is below 0.80, revise the rules that caused the disagreements, record
   the revision in this file, and recode all countries affected by the revised rule.
5. Resolve the remaining disagreements by discussion, and record each one in
   `data/rollout/resolution_log.csv` (iso3, field, value coder 1, value coder 2, resolution, reason).
6. Report the agreement statistics before resolution in the paper.

## 8. Validation

`python -m idsp.coding validate` checks required columns, year ranges, binary fields, and the
two-source rule for rows with `status = final`. The panel builder refuses to run while
problems remain.
