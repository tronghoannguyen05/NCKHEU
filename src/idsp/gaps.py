"""Within-country gaps in benefit receipt (H2, distributional effect).

Gap = advantaged group minus disadvantaged group, in percentage points. A positive ATT on a gap
means the gap widened after rollout, which is what H2 predicts.
"""

from __future__ import annotations

import pandas as pd

GAPS = {
    "gap_sex": ("transfer_male", "transfer_female"),
    "gap_income": ("transfer_rich60", "transfer_poor40"),
    "gap_residence": ("transfer_urban", "transfer_rural"),
}


def add_gaps(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for name, (adv, dis) in GAPS.items():
        if adv in out and dis in out:
            out[name] = out[adv] - out[dis]
    return out
