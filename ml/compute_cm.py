import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.train_optimized import (
    SOURCE_DATA,
    STOPWORDS_FILE,
    classify_hostel_category,
)
from backend.app.services.text_preprocessing import preprocess_complaint_text


def _held_out_data() -> tuple[pd.DataFrame, frozenset[str]]:
    df = pd.read_csv(SOURCE_DATA).dropna(subset=["complaint", "priority"]).copy()
    df["complaint"] = df["complaint"].astype(str)
    df["complaint_norm"] = df["complaint"].str.strip().str.lower()
    df = df.drop_duplicates(subset=["complaint_norm"], keep="first").copy()
    df["hostel_category"] = df["complaint"].map(classify_hostel_category)
    stop_words = frozenset(
        word.strip()
        for word in STOPWORDS_FILE.read_text(encoding="utf-8").splitlines()
        if word.strip()
    )
    df["complaint_proc"] = df["complaint"].map(
        lambda text: preprocess_complaint_text(text, stop_words)
    )
    df = df[df["complaint_proc"].str.len() > 0].copy()
    _, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["hostel_category"],
    )
    return test_df, stop_words


def _compute_cm(target: str, model_name: str):
    test_df, stop_words = _held_out_data()
    vectorizer = joblib.load(ROOT / "ml" / "models" / "tfidf.pkl")
    model = joblib.load(ROOT / "ml" / "models" / model_name)
    texts = test_df["complaint"].map(
        lambda text: preprocess_complaint_text(text, stop_words)
    )
    features = vectorizer.transform(texts)
    y_true = test_df[target].to_numpy()
    y_pred = model.predict(features)
    labels = sorted(set(model.classes_))
    return labels, confusion_matrix(y_true, y_pred, labels=labels), y_true, y_pred


def compute_category_cm():
    return _compute_cm("hostel_category", "category.pkl")


def compute_priority_cm():
    return _compute_cm("priority", "priority.pkl")


if __name__ == "__main__":
    labels_cat, cm_cat, y_true_cat, y_pred_cat = compute_category_cm()
    print("Category labels:", labels_cat)
    print("Category confusion matrix:\n", cm_cat)

    errors = []
    for i, actual in enumerate(labels_cat):
        for j, predicted in enumerate(labels_cat):
            if i != j and cm_cat[i, j] > 0:
                errors.append(((actual, predicted), int(cm_cat[i, j])))
    errors.sort(key=lambda item: item[1], reverse=True)
    print("Most common category errors (actual->predicted, count):", errors[:10])

    labels_prio, cm_prio, y_true_prio, y_pred_prio = compute_priority_cm()
    print("\nPriority labels:", labels_prio)
    print("Priority confusion matrix:\n", cm_prio)

    errors_pr = []
    for i, actual in enumerate(labels_prio):
        for j, predicted in enumerate(labels_prio):
            if i != j and cm_prio[i, j] > 0:
                errors_pr.append(((actual, predicted), int(cm_prio[i, j])))
    errors_pr.sort(key=lambda item: item[1], reverse=True)
    print("Most common priority errors (actual->predicted, count):", errors_pr[:10])
