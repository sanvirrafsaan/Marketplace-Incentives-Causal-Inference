# Environment setup

This document explains how the project environment is configured and **why** each choice was made.

---

## Quick start

```bash
cd Marketplace-Incentives-Causal-Inference

# Activate the virtual environment (created at repo root)
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

# Confirm imports
python -c "import duckdb, pandas, statsmodels, scipy; print('OK')"

# Optional: Jupyter for notebooks
jupyter lab
# or: jupyter notebook
```

**Data (you still need to do this):** download [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and place all CSV files in `data/raw/olist/`. Those files are gitignored because they are large and licensed via Kaggle.

---

## What was set up in the repo

| Artifact | Purpose |
|----------|---------|
| `.venv/` | Isolated Python environment (local only, gitignored) |
| `requirements.txt` | Pinned dependencies for reproducibility |
| `.gitignore` | Keeps data, DBs, secrets, and venv out of Git |
| `data/raw/olist/` | Standard location for Kaggle CSVs |
| `notebooks/`, `sql/`, `docs/`, `scripts/` | Empty dirs with `.gitkeep` so structure exists on clone |

---

## Engineering decisions

### 1. Virtual environment (`.venv` at repo root)

**Choice:** Standard library `venv` in `.venv/`, not conda, not global pip.

**Why:**

- **Reproducibility:** Anyone cloning the repo gets the same dependency set via `pip install -r requirements.txt`.
- **Isolation:** Avoids conflicts with other projects on your machine.
- **Convention:** `.venv` is widely recognized; IDEs (Cursor/VS Code) auto-detect it.

**Trade-off:** Conda is better if you need heavy geospatial/CUDA stacks; this project does not.

---

### 2. DuckDB (not SQLite) for analytics

**Choice:** DuckDB as the analytical database (`data/olist.db` when you create it).

**Why:**

- **Speed:** Columnar engine; fast aggregations and joins on ~100K-order scale.
- **SQL + Python:** Query from notebooks with `duckdb.connect('data/olist.db')` or in-memory `duckdb.sql("SELECT ... FROM df")`.
- **Analytics features:** Window functions, `read_csv_auto`, easy `CREATE TABLE AS` for your `orders_analytical` mart.
- **Single file:** One `.db` file is easy to regenerate from raw CSVs (and we gitignore it).

**Trade-off:** SQLite is fine for tiny demos; DuckDB is the better default for DS portfolio SQL work.

---

### 3. `requirements.txt` with version pins

**Choice:** Pin major/minor versions after a working install.

**Why:**

- Recruiters or future-you running `pip install -r requirements.txt` get a similar stack months later.
- Reduces “works on my machine” drift for `statsmodels` / `scipy` / `duckdb`.

**Trade-off:** Occasional `pip install --upgrade` when you need security fixes; bump pins intentionally.

**Core packages:**

| Package | Role |
|---------|------|
| `pandas` | Tables, light transforms |
| `duckdb` | SQL engine and persistence |
| `jupyter` / `ipykernel` | Notebooks |
| `matplotlib`, `seaborn`, `plotly` | EDA and parallel-trends plots |
| `scipy` | Bootstrap CIs |
| `statsmodels` | DiD regression extensions, power analysis (Week 4) |

---

### 4. `.gitignore` for data and databases

**Choice:** Ignore `data/raw/`, `*.csv`, `*.db`, `.kaggle/`, `.env`.

**Why:**

- Olist is tens of MB; GitHub is not a data store.
- Kaggle terms and API tokens should not be committed.
- `olist.db` is **derived**—rebuild from notebooks + raw CSVs.

**What *is* committed:** structure (`.gitkeep`), SQL files, notebooks, docs, `requirements.txt`.

---

### 5. Folder layout: `sql/` and `scripts/` separate from `notebooks/`

**Choice:** Optional `sql/01_master_order.sql` and `scripts/power_analysis.py` instead of stuffing everything in notebooks.

**Why:**

- **Resume signal:** Shows you treat SQL and analysis code as reusable assets.
- **Testing:** Small scripts are easier to re-run than scrolling notebook cells.
- **Notebooks stay narrative:** Load → query → plot → interpret.

You can still keep SQL in notebook cells early on; extract to `sql/` when a query stabilizes.

---

### 6. No pre-built notebooks for analysis weeks

**Choice:** Only scaffolding; you author `01`–`03` notebooks.

**Why:** The learning and interview story depend on **your** decisions (on-time definition, regions, DiD checks). Pre-filled notebooks weaken that.

---

## Kaggle download (manual steps)

**Option A — Browser**

1. Log in at [dataset page](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
2. Download and unzip into `data/raw/olist/`.

**Option B — Kaggle CLI**

```bash
pip install kaggle   # inside activated .venv if you like
# Place kaggle.json in ~/.kaggle/ (chmod 600)
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/olist --unzip
```

**Expected files (9 tables):**  
`olist_orders_dataset.csv`, `olist_order_items_dataset.csv`, `olist_customers_dataset.csv`, `olist_sellers_dataset.csv`, `olist_products_dataset.csv`, `olist_geolocation_dataset.csv`, `olist_order_payments_dataset.csv`, `olist_order_reviews_dataset.csv`, `product_category_name_translation.csv`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `command not found: python` | Use `python3` when creating venv |
| Wrong interpreter in Jupyter | `python -m ipykernel install --user --name=marketplace-causal` |
| DuckDB lock on DB file | Close other connections / restart kernel |
| Import errors after pull | `pip install -r requirements.txt` in activated venv |

---

## Python version

Use **Python 3.10+** (3.11–3.12 are common; this repo’s `.venv` was created with **3.14** on your machine). Check with:

```bash
python3 --version
```

If you recreate the venv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
