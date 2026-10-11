# Project Activity Log — Smart Hostel Maintenance

This log records each step we (you and the assistant) perform during the project. Append new entries chronologically.

---

## Summary (so far)

- **2026-08-12  — Read project implementation plan**
  - File: [Smart_Hostel_Implementation_Plan.md](Smart_Hostel_Implementation_Plan.md)
  - Action: Reviewed the full implementation specification and architecture.

- **2026-08-12  — Inspected dataset sample**
  - File: [hotel_maintenance_dataset.csv](hotel_maintenance_dataset.csv#L1-L199)
  - Action: Sampled the CSV to confirm fields: `complaint`, `category`, `priority`, and others.

- **2026-08-12  — Assessed feasibility and constraints**
  - Action: Confirmed project is feasible with the chosen stack; noted label variations (`urgent`, `routine`, `cosmetic`) and possible class imbalance. Recommended EDA, label normalization options, and a training prototype using TF-IDF + Logistic Regression.

- **2026-08-12  — Created project activity log**
  - File: [PROJECT_ACTIVITY_LOG.md](PROJECT_ACTIVITY_LOG.md)

- **2026-08-12  — Added preprocessing and data-prep scripts**
  - Files: [ml/preprocessing.py](ml/preprocessing.py#L1-L200), [ml/prepare_data.py](ml/prepare_data.py#L1-L200)
  - Action: Implemented `preprocess_text()` using NLTK and a `prepare_dataset` script that standardizes `priority` to High/Medium/Low, removes duplicates and empty complaints, and will write `ml/dataset/cleaned_hotel_maintenance_dataset.csv` when run.

- **2026-08-12  — Ran data preparation script**
  - Script: [ml/prepare_data.py](ml/prepare_data.py#L1-L200)
  - Output: `ml/dataset/cleaned_hotel_maintenance_dataset.csv`
  - Notes: 1500 rows input; priority standardized counts -> Medium:679, High:450, Low:371; top categories reported.

- **2026-08-12  — Trained models (prototype)**
  - Script: [ml/train.py](ml/train.py#L1-L200)
  - Artifacts saved: `ml/models/tfidf.pkl`, `ml/models/category.pkl`, `ml/models/priority.pkl`
  - Results (test set, 20%):
    - Category model accuracy ~29% (per-class F1s vary; rare classes low support).
    - Priority model accuracy ~99% (likely because `priority` words are present in text or easily separable).
  - Recommendation: Improve category performance by expanding data, consolidating similar categories, adding domain-specific features, or using stronger models.

- **2026-08-12  — Analyzed and tuned ML pipeline**
  - Script: [ml/analyze_and_tune.py](ml/analyze_and_tune.py#L1-L200)
  - Output: [ml/analysis_summary.md](ml/analysis_summary.md)
  - Findings:
    - Category baseline accuracy 0.2567 → tuned accuracy 0.2833.
    - Priority baseline accuracy 0.9933 → tuned accuracy 0.9967.
    - Priority target leakage: 27.11% of High complaints include the word `urgent`.
    - Exact complaint overlap between train/test: 23 rows.
    - Top category confusions include Electrical→Plumbing, General→Landscaping, Furniture→Internet/AV.
  - Saved tuned pipelines: `ml/models/category_tuned_pipeline.pkl`, `ml/models/priority_tuned_pipeline.pkl`.

---

## How to use this log

- Add a single line entry for each meaningful action (date, brief action, files changed, short result).
- When running scripts or training runs, include the command used and resulting metrics.
- Keep the `preprocess_text()` implementation and model artifact filenames referenced here when they are created.

## Pending / Future entries

- EDA: full label counts, missing values, class balance.
- Implement `preprocess_text(text)` and record code path.
- Train TF-IDF and Logistic Regression models; record training metrics and artifact filenames `tfidf.pkl`, `category.pkl`, `priority.pkl`.
- Add API integration and record endpoint paths and deployment notes.

---

_Log created by the assistant on request from the user._
