"""Write tables, event-study figures and the input file for r/honestdid.R."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def write_table(df: pd.DataFrame, path: Path, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out.insert(0, "data", label)
    out.to_csv(path, index=False, float_format="%.4f")


def event_study_plot(dyn: pd.DataFrame, path: Path, title: str, label: str, xlabel: str,
                     window: tuple[int, int] | None = None) -> None:
    d = dyn.dropna(subset=["att"])
    if window:
        d = d[(d["event_time"] >= window[0]) & (d["event_time"] <= window[1])]
    fig, ax = plt.subplots(figsize=(7, 4))
    e = d["event_time"].to_numpy()
    ax.axhline(0, color="#555555", lw=0.8)
    ax.axvline(-0.5, color="#999999", lw=0.8, ls="--")
    ax.fill_between(e, d["ci_low"], d["ci_high"], color="#4C72B0", alpha=0.18, lw=0,
                    label="95% simultaneous band")
    ax.plot(e, d["att"], "o-", color="#1f3b73", ms=4, lw=1.4, label="ATT by event time")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Percentage points")
    ax.set_title(f"{title}\n[{label}]", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def honestdid_export(cs_universal, path: Path, post_average_e: list[int], label: str) -> None:
    """Event-study coefficients (universal base) and bootstrap covariance for HonestDiD.

    The reference period e = -1 is excluded. ``l_vec`` averages the post-period effects listed in
    ``post_average_e``.
    """
    est, cov = cs_universal.event_study_vcov()
    est = est.drop(index=-1, errors="ignore")
    cov = cov.drop(index=-1, columns=-1, errors="ignore")
    e = est.index.to_numpy()
    pre, post = e[e < 0], e[e >= 0]
    l_vec = np.array([1.0 if x in post_average_e else 0.0 for x in post])
    if l_vec.sum() == 0:
        raise ValueError("None of post_average_e is estimated.")
    l_vec = l_vec / l_vec.sum()
    payload = dict(data=label, event_time=e.tolist(), betahat=est.to_numpy().tolist(),
                   sigma=cov.to_numpy().tolist(), numPrePeriods=int(len(pre)),
                   numPostPeriods=int(len(post)), l_vec=l_vec.tolist())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1))
