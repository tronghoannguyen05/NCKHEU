"""Paths and settings."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
DATA = ROOT / "data"
RAW = DATA / "raw"
MANUAL = RAW / "manual"
PROCESSED = DATA / "processed"
ROLLOUT = DATA / "rollout"
OUTPUT = ROOT / "output"


def load(name: str = "settings") -> dict:
    with open(CONFIG / f"{name}.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
