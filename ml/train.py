import os
from pathlib import Path
import joblib
import sys
from pathlib import Path

# Ensure project root is on sys.path so ml package imports resolve when running the script directly
sys.path.append(str(Path(__file__).resolve().parents[1]))
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from ml.preprocessing import preprocess_text


def load_data(path: Path):
    df = pd.read_csv(path)
    df = df.dropna(subset=["complaint", "category", "priority"]) 
    df["complaint_proc"] = df["complaint"].astype(str).apply(preprocess_text)
    return df


def train_and_save(df, out_dir: Path):
    X = df["complaint_proc"].values
    y_cat = df["category"].values
    y_prio = df["priority"].values

    X_train, X_test, y_cat_train, y_cat_test, y_prio_train, y_prio_test = train_test_split(
        X, y_cat, y_prio, test_size=0.2, random_state=42, stratify=y_cat
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    # TF-IDF
    tfidf = TfidfVectorizer(max_features=10000)
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)

    joblib.dump(tfidf, out_dir / "tfidf.pkl")

    # Category model
    cat_clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    cat_clf.fit(X_train_tfidf, y_cat_train)
    y_cat_pred = cat_clf.predict(X_test_tfidf)
    print("\nCategory classification report:\n")
    print(classification_report(y_cat_test, y_cat_pred, zero_division=0))
    joblib.dump(cat_clf, out_dir / "category.pkl")

    # Priority model
    prio_clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    prio_clf.fit(X_train_tfidf, y_prio_train)
    y_prio_pred = prio_clf.predict(X_test_tfidf)
    print("\nPriority classification report:\n")
    print(classification_report(y_prio_test, y_prio_pred, zero_division=0))
    joblib.dump(prio_clf, out_dir / "priority.pkl")

    print(f"Models and vectorizer saved to: {out_dir}")


def main():
    root = Path(__file__).resolve().parents[1]
    data_path = root / "ml" / "dataset" / "cleaned_hotel_maintenance_dataset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found: {data_path}")

    df = load_data(data_path)
    out_dir = root / "ml" / "models" / "legacy_hotel"
    train_and_save(df, out_dir)


if __name__ == "__main__":
    main()
