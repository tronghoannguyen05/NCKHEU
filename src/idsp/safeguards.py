"""Rights-safeguard index (H3 moderator).

The proposal proxies safeguards by a data protection law, government accountability (WGI voice
and accountability, rule of law) and civic space (V-Dem). Components are measured in a fixed
baseline year so that the moderator precedes rollout for every cohort in the estimation window
and is defined for control countries as well (see docs/review_notes.md, item on timing).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def safeguard_index(countries: pd.DataFrame, components: list[str], baseline_year: int,
                    dp_law_col: str | None = "dp_law_year", split: str = "median") -> pd.DataFrame:
    """Return iso3, the standardized composite ``safeguard`` and the binary ``high_safeguard``.

    components: continuous baseline columns (already measured at ``baseline_year``).
    dp_law_col: year a data protection law entered into force; converted to a 0/1 indicator
    of a law in force at the baseline year and added as a component.
    """
    d = countries[["iso3"] + components + ([dp_law_col] if dp_law_col else [])].copy()
    cols = list(components)
    if dp_law_col:
        d["dp_law_in_force"] = (d[dp_law_col] <= baseline_year).astype(float)
        cols.append("dp_law_in_force")
    z = (d[cols] - d[cols].mean()) / d[cols].std(ddof=0)
    d["safeguard"] = z.mean(axis=1, skipna=False)
    if split == "median":
        cut = d["safeguard"].median()
        d["high_safeguard"] = np.where(d["safeguard"].isna(), np.nan, (d["safeguard"] > cut).astype(float))
    elif split == "tercile":
        q = d["safeguard"].quantile([1 / 3, 2 / 3]).to_numpy()
        d["high_safeguard"] = np.select([d["safeguard"] <= q[0], d["safeguard"] > q[1]], [0.0, 1.0], np.nan)
    else:
        raise ValueError("split must be 'median' or 'tercile'.")
    return d[["iso3", "safeguard", "high_safeguard"] + cols]
