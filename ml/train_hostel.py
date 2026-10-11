import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

EVAL_DIR = ROOT / "ml" / "evaluation"
MODELS_DIR = ROOT / "ml" / "models"
EVAL_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_hostel_dataset(path: Path):
    df = pd.read_csv(path)
    # Expect columns: complaint, hostel_category, priority
    # Ensure complaint text is string
    df['complaint'] = df['complaint'].astype(str)
    # Import preprocessing after sys.path has been set so package imports resolve
    from ml.preprocessing import preprocess_text
    # Recompute preprocessing using canonical preprocess_text() to ensure consistency
    df['complaint_proc'] = df['complaint'].apply(preprocess_text)
    # Normalized complaint for exact-duplicate detection (case-insensitive exact match)
    df['complaint_norm'] = df['complaint'].str.strip().str.lower()
    return df


def analyze_dataset(df: pd.DataFrame):
    total = len(df)
    counts = df['hostel_category'].value_counts()
    pct = (counts / total * 100).round(2)
    missing = df.isnull().sum().to_dict()

    exact_duplicates = df['complaint'].astype(str).str.strip().str.lower().duplicated().sum()
    near_duplicates = df['complaint_proc'].duplicated().sum() if 'complaint_proc' in df.columns else 0

    summary = {
        'total_records': int(total),
        'category_counts': counts.to_dict(),
        'category_percentages': pct.to_dict(),
        'missing_values': missing,
        'exact_duplicate_complaints': int(exact_duplicates),
        'near_duplicate_complaints': int(near_duplicates),
    }
    return summary


def ensure_no_overlap(train_df, test_df):
    train_texts = set(train_df['complaint'].astype(str).str.strip().str.lower())
    test_texts = set(test_df['complaint'].astype(str).str.strip().str.lower())
    overlap = train_texts & test_texts
    return overlap


def plot_and_save_confusion(cm, labels, out_path: Path, title: str):
    plt.figure(figsize=(8,6))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=labels, yticklabels=labels, cmap='Blues')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def main():
    data_path = ROOT / 'ml' / 'dataset' / 'dataset_hostel.csv'
    if not data_path.exists():
        raise FileNotFoundError(f"Hostel dataset not found: {data_path}")

    df = load_hostel_dataset(data_path)
    summary = analyze_dataset(df)
    (ROOT / 'ml' / 'analysis_summary_hostel.json').write_text(json.dumps(summary, indent=2))
    print('Dataset analysis saved to ml/analysis_summary_hostel.json')

    # Remove any remaining exact duplicates based on normalized raw complaint (keep first)
    before = len(df)
    df = df.drop_duplicates(subset=['complaint_norm'], keep='first')
    after = len(df)
    duplicate_count = before - after

    # Prepare inputs and targets
    X_all = df['complaint_proc'].astype(str)
    y_cat_all = df['hostel_category'].values
    y_prio_all = df['priority'].values

    # Split using the raw complaint normalization to ensure exact complaint texts do not cross splits
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df['hostel_category']
    )

    # Verify no exact overlap on raw complaint text
    overlap = ensure_no_overlap(train_df[['complaint']], test_df[['complaint']])
    if overlap:
        raise RuntimeError(f"Found exact overlap between train and test complaints: {len(overlap)}")

    X_train = train_df['complaint_proc'].astype(str).values
    X_test = test_df['complaint_proc'].astype(str).values
    y_cat_train = train_df['hostel_category'].values
    y_cat_test = test_df['hostel_category'].values
    y_prio_train = train_df['priority'].values
    y_prio_test = test_df['priority'].values

    # Category pipeline grid search (tfidf + logistic)
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('clf', LogisticRegression(max_iter=2000, solver='saga', class_weight='balanced')),
    ])

    param_grid = {
        'tfidf__ngram_range': [(1,1),(1,2)],
        'tfidf__min_df': [1,2,3],
        'tfidf__max_df': [0.9,0.95,1.0],
        'clf__C': [0.1,1.0,10.0]
    }

    gs = GridSearchCV(pipeline, param_grid, cv=3, scoring='f1_macro', n_jobs=-1, verbose=0)
    # Fit grid-search only on training data (no access to test set)
    gs.fit(X_train, y_cat_train)
    best = gs.best_estimator_
    print('Best category params:', gs.best_params_)

    # Extract and save shared TF-IDF and category classifier
    tfidf = best.named_steps['tfidf']
    cat_clf = best.named_steps['clf']
    joblib.dump(tfidf, MODELS_DIR / 'tfidf.pkl')
    joblib.dump(cat_clf, MODELS_DIR / 'category.pkl')
    print('Saved tfidf and category model')

    # Evaluate category on test set (transform using the shared tfidf fitted from training)
    X_test_tfidf = tfidf.transform(X_test)
    y_cat_pred = cat_clf.predict(X_test_tfidf)
    cat_report = classification_report(y_cat_test, y_cat_pred, output_dict=True, zero_division=0)
    (EVAL_DIR / 'category_report.json').write_text(json.dumps(cat_report, indent=2))
    labels_cat = list(sorted(set(y_cat_test)))
    cm_cat = confusion_matrix(y_cat_test, y_cat_pred, labels=labels_cat)
    plot_and_save_confusion(cm_cat, labels_cat, EVAL_DIR / 'category_confusion_matrix.png', 'Category Confusion Matrix')

    # Priority model: use the same tfidf (shared). Tune only LogisticRegression C using CV on training set
    X_train_tfidf = tfidf.transform(X_train)
    param_grid_prio = {'C': [0.1,1.0,10.0]}
    prio_gs = GridSearchCV(LogisticRegression(max_iter=2000, solver='saga', class_weight='balanced'), param_grid_prio, cv=3, scoring='f1_macro', n_jobs=-1)
    prio_gs.fit(X_train_tfidf, y_prio_train)
    prio_clf = prio_gs.best_estimator_
    joblib.dump(prio_clf, MODELS_DIR / 'priority.pkl')
    print('Saved priority model')

    y_prio_pred = prio_clf.predict(X_test_tfidf)
    prio_report = classification_report(y_prio_test, y_prio_pred, output_dict=True, zero_division=0)
    (EVAL_DIR / 'priority_report.json').write_text(json.dumps(prio_report, indent=2))
    labels_prio = list(sorted(set(y_prio_test)))
    cm_prio = confusion_matrix(y_prio_test, y_prio_pred, labels=labels_prio)
    plot_and_save_confusion(cm_prio, labels_prio, EVAL_DIR / 'priority_confusion_matrix.png', 'Priority Confusion Matrix')

    # Save train/test splits with raw complaint and preprocessed columns
    train_df_out = train_df[['complaint', 'complaint_proc', 'hostel_category', 'priority']].copy()
    test_df_out = test_df[['complaint', 'complaint_proc', 'hostel_category', 'priority']].copy()
    train_df_out.to_csv(ROOT / 'ml' / 'dataset' / 'train_hostel.csv', index=False)
    test_df_out.to_csv(ROOT / 'ml' / 'dataset' / 'test_hostel.csv', index=False)

    # Save summary
    summary_out = {
        'original_record_count': int(summary['total_records']),
        'final_record_count': int(len(df)),
        'category_distribution': {k:int(v) for k,v in summary['category_counts'].items()},
        'train_size': int(len(train_df_out)),
        'test_size': int(len(test_df_out)),
        'category_best_params': gs.best_params_,
        'priority_best_params': {'C': prio_gs.best_params_['C']}
    }
    (ROOT / 'ml' / 'training_summary_hostel.json').write_text(json.dumps(summary_out, indent=2))
    print('Training and evaluation complete. Artifacts and reports saved under ml/models and ml/evaluation')

if __name__ == '__main__':
    main()
