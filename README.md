# Marketplace Incentives & Causal Inference

End-to-end analytics and causal inference on [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) data: multi-table SQL pipeline, simulated regional incentive rollout, difference-in-differences with bootstrap confidence intervals, and a prospective experiment design.

**Status:** In progress (Week 0 — environment ready; analysis notebooks not started)

## Documentation

| Doc | Description |
|-----|-------------|
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | 5-week roadmap, deliverables, learning resources |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | Local setup, tooling choices, Kaggle download |

## Quick start

```bash
source .venv/bin/activate
pip install -r requirements.txt   # if you recreate the venv
```

Download dataset CSVs to `data/raw/olist/` (see [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)), then start with `notebooks/01_data_ingestion.ipynb`.

## Tech stack

Python · DuckDB · pandas · scipy · statsmodels · Jupyter · Matplotlib / Seaborn / Plotly

## Resume (in progress)

Building a multi-table SQL/Python analytics pipeline on marketplace logistics data and applying difference-in-differences with bootstrap confidence intervals to evaluate a simulated regional incentive rollout, quantifying effects on on-time delivery, customer satisfaction, and unit economics.
