# data/raw

Not tracked by git (except this file). Regenerate:

- `wb_*.csv`: `python -m idsp.data.worldbank` (World Bank API: WDI and WGI).
- `manual/*.csv`: downloaded by hand and saved in the tidy schema listed in `config/sources.yaml`.
  Step-by-step instructions are in `docs/data_sources.md`.

All sources are public. Keep the original downloads (with their download date) in
`data/raw/original/` so that every tidy file can be traced back to its source.
