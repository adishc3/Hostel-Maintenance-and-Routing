import joblib
import json
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from ml.preprocessing import preprocess_text

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / 'ml' / 'models'
EVAL_DIR = ROOT / 'ml' / 'evaluation'
MODELS_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)


def load_splits():
    train = pd.read_csv(ROOT / 'ml' / 'dataset' / 'train_hostel.csv')
    test = pd.read_csv(ROOT / 'ml' / 'dataset' / 'test_hostel.csv')
    # Ensure complaint text is string and preprocess to be safe
    train['complaint_proc'] = train['complaint'].astype(str).apply(preprocess_text)
    test['complaint_proc'] = test['complaint'].astype(str).apply(preprocess_text)
    return train, test


def train_baseline():
    train, test = load_splits()
    X_train = train['complaint_proc'].astype(str).values
    X_test = test['complaint_proc'].astype(str).values
    y_cat_train = train['hostel_category'].values
    y_cat_test = test['hostel_category'].values
    y_prio_train = train['priority'].values
    y_prio_test = test['priority'].values

    # Fit TF-IDF on training only
    tfidf = TfidfVectorizer()
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)
    joblib.dump(tfidf, MODELS_DIR / 'tfidf_baseline.pkl')

    # Baseline category model (default LogisticRegression)
    cat_clf = LogisticRegression(max_iter=1000)
    cat_clf.fit(X_train_tfidf, y_cat_train)
    y_cat_pred = cat_clf.predict(X_test_tfidf)
    cat_report = classification_report(y_cat_test, y_cat_pred, output_dict=True, zero_division=0)
    (EVAL_DIR / 'category_report_baseline.json').write_text(json.dumps(cat_report, indent=2))
    joblib.dump(cat_clf, MODELS_DIR / 'category_baseline.pkl')
    cm_cat = confusion_matrix(y_cat_test, y_cat_pred, labels=sorted(set(y_cat_test)))

    # Baseline priority model
    prio_clf = LogisticRegression(max_iter=1000)
    prio_clf.fit(X_train_tfidf, y_prio_train)
    y_prio_pred = prio_clf.predict(X_test_tfidf)
    prio_report = classification_report(y_prio_test, y_prio_pred, output_dict=True, zero_division=0)
    (EVAL_DIR / 'priority_report_baseline.json').write_text(json.dumps(prio_report, indent=2))
    joblib.dump(prio_clf, MODELS_DIR / 'priority_baseline.pkl')
    cm_prio = confusion_matrix(y_prio_test, y_prio_pred, labels=sorted(set(y_prio_test)))

    # Save confusion matrices as numpy arrays for quick inspection
    joblib.dump({'labels': sorted(set(y_cat_test)), 'cm': cm_cat}, EVAL_DIR / 'category_confusion_baseline.pkl')
    joblib.dump({'labels': sorted(set(y_prio_test)), 'cm': cm_prio}, EVAL_DIR / 'priority_confusion_baseline.pkl')

    print('Baseline training complete. Baseline reports saved.')


if __name__ == '__main__':
    train_baseline()
