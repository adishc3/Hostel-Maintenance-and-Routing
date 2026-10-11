# ML Analysis and Tuning Summary

## 1. Dataset review

- Total rows after cleaning: 1500
- Priority distribution:
  - Medium: 679
  - High: 450
  - Low: 371
- Category distribution:
  - Electrical: 186
  - Plumbing: 171
  - Appliance: 155
  - Structural: 146
  - General: 145
  - Safety/Security: 133
  - Furniture: 125
  - HVAC: 110
  - Internet/AV: 97
  - Housekeeping: 86
  - Elevator: 52
  - Pool/Water Feature: 44
  - Landscaping: 40
  - Pest Control: 10

## 2. Target leakage check

- High: 122/450 complaints contain the literal word `urgent` (27.11%)
- Medium: 0/679 complaints contain `routine` (0.00%)
- Low: 0/371 complaints contain `cosmetic` (0.00%)

The priority model does have some leakage from the `urgent` keyword, but the majority of High examples do not contain the exact word.

## 3. Duplicate and overlap checks

- Exact duplicate rows in the cleaned dataset: 0
- Near-duplicate complaints after preprocessing: 59
- Exact complaint text overlap between train and test: 23

There is a small amount of train/test overlap in complaint text, which should be addressed before final evaluation if strict generalization is required.

## 4. Preprocessing and train/test split verification

- Preprocessing function: `ml/preprocessing.py::preprocess_text()`
- Pipeline uses the same preprocessing for training and evaluation.
- Train/test split is done with `train_test_split(..., random_state=42, stratify=y_cat)`.
- TF-IDF is fit on `X_train` and transformed on `X_test`.

## 5. Baseline TF-IDF + Logistic Regression

### Category model (baseline)
- Accuracy: 0.2567
- Macro F1: 0.2761
- Weighted F1: 0.2409

### Priority model (baseline)
- Accuracy: 0.9933
- Macro F1: 0.9931
- Weighted F1: 0.9933

## 6. Category confusion patterns

Top category confusions:
- Electrical → Plumbing (8 examples)
- General → Landscaping (8 examples)
- Furniture → Internet/AV (7 examples)
- Plumbing → HVAC (7 examples)
- Safety/Security → Pool/Water Feature (7 examples)
- Appliance → Internet/AV (6 examples)
- Appliance → Plumbing (6 examples)
- General → Housekeeping (6 examples)
- HVAC → Internet/AV (6 examples)
- Housekeeping → Furniture (6 examples)

This indicates many category confusions occur between similar service areas and general utility complaint language.

## 7. Priority confusion patterns

- The model only confused Medium → Low in 2 cases.
- High and Low were otherwise perfectly separated on the held-out set.

## 8. Tuning results

### Category model (tuned)
- Best TF-IDF / LogisticRegression params:
  - `tfidf__ngram_range`: (1, 2)
  - `tfidf__min_df`: 3
  - `tfidf__max_df`: 0.95
  - `clf__C`: 10.0
- Accuracy: 0.2833
- Macro F1: 0.3072
- Weighted F1: 0.2758

### Priority model (tuned)
- Best params:
  - `tfidf__ngram_range`: (1, 2)
  - `tfidf__min_df`: 1
  - `tfidf__max_df`: 0.9
  - `clf__C`: 10.0
- Accuracy: 0.9967
- Macro F1: 0.9965
- Weighted F1: 0.9967

## 9. Old vs. new metrics (same held-out test set)

- Category accuracy improved from 0.2567 to 0.2833.
- Priority accuracy improved from 0.9933 to 0.9967.

## 10. Notes

- The category model is still weak due to many overlapping and semantically similar classes.
- The priority model is extremely strong, but some of the strength may be influenced by text patterns like `urgent`.
- The tuned pipelines were saved to `ml/models/category_tuned_pipeline.pkl` and `ml/models/priority_tuned_pipeline.pkl`.
