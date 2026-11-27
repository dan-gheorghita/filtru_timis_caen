# filtru_timis_caen.py

This Python script implements a four-stage streaming pipeline to filter Romanian companies by county and then by authorized economic activity codes (CAEN). Here's what it does:

**Overall purpose:**  
Start with a massive company registry, narrow it down to firms in a specific county, attach their approved CAEN (industrial activity) codes, and finally keep only those matching a predefined list of CAEN codes.

**Step-by-step breakdown:**

1. **County filter** – Reads the full company CSV (`od_firme_*.csv`), normalizes the `ADR_JUDET` field (handles diacritics/case: `Timiş`, `Timiș`, `TIMIS` → `timis`), and writes only Timis-based firms to a new file. It also collects each company's internal ID (`COD_INMATRICULARE`) for the next step.

2. **CAEN lookup** – Streams the CAEN authorization file (`od_caen_autorizat_*.csv`), matches rows against the Timis company IDs collected in step 1, and builds a mapping of `company_id → [(caen_code, version), ...]`.

3. **Code attachment** – Reads the Timis-filtered file from step 1 and appends the matching CAEN codes (and versions) to each company record. Output format is configurable: either all codes on one line semicolon-separated, or one line per code (company repeated).

4. **Final CAEN filter** – Keeps only companies that have *at least one* CAEN code from a user-defined list (default: `6110;6120;6210;6220;6290;6310;6391;6392`). The other codes are ignored if the filter string is left empty. Writes the final filtered dataset.

**Key configurable settings (at the top of the script):**
- Input/output file paths (Windows absolute paths)
- Target county (`JUDET = "Timis"`)
- File encoding and column separator (`^`)
- CAEN filter codes (`CODURI_CAEN_FILTRU`)
- Output format (`FORMAT_LONG`)
- Normalization handles `Timiş`/`Timiș`/`TIMIS` uniformly

**Output files:**
- `od_firme_Timis_04.11.2026.csv` – Timis firms only
- `firme_timis_caen.csv` – Timis firms with their CAEN codes attached
- `firme_timis_filtrat_caen.csv` – Final list: only Timis firms holding at least one requested CAEN code

The script is optimized for memory-efficient processing of multi-million-line CSVs using streaming I/O and a cached normalization lookup for the county filter.