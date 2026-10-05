PY ?= python

.PHONY: install test synthetic download build analysis honestdid

install:
	$(PY) -m pip install -e ".[dev]"

test:
	$(PY) -m pytest

# End-to-end run on synthetic data (no downloads needed). Outputs are labelled SYNTHETIC.
synthetic:
	$(PY) -m idsp.pipeline --synthetic

# Fetch the sources that have an API (World Bank WDI/WGI). Other sources are manual: see docs/data_sources.md.
download:
	$(PY) -m idsp.data.worldbank

# Build data/processed/panel_country_year.csv and panel_country_wave.csv from data/raw and data/rollout.
build:
	$(PY) -m idsp.data.panel

analysis:
	$(PY) -m idsp.pipeline

# Rambachan-Roth sensitivity (requires R with HonestDiD and jsonlite).
honestdid:
	Rscript r/honestdid.R
