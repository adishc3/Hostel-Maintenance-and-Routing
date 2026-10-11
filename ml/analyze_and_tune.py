import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, train_test_split

# Ensure project root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from ml.preprocessing import preprocess_text


def load_data(path: Path):
    df = pd.read_csv(path)
    df = df.dropna(subset=["complaint", "category", "priority"])
    df["complaint_proc"] = df["complaint"].astype(str).apply(preprocess_text)
    return df


def inspect_distribution(df: pd.DataFrame):
    print("=== Class Distribution ===")
    print("Category distribution:")
    print(df["category"].value_counts(dropna=False).sort_values(ascending=False))
    print("\nPriority distribution:")
    print(df["priority"].value_counts(dropna=False).sort_values(ascending=False))
    print()


def split_data(df: pd.DataFrame):
    X = df["complaint_proc"].values
    y_cat = df["category"].values
    y_prio = df["priority"].values
    X_train, X_test, y_cat_train, y_cat_test, y_prio_train, y_prio_test = train_test_split(
        X,
        y_cat,
        y_prio,
        test_size=0.2,
        random_state=42,
        stratify=y_cat,
    )
    return X_train, X_test, y_cat_train, y_cat_test, y_prio_train, y_prio_test


def compute_confusion(y_true, y_pred, labels, title):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print(f"=== {title} Confusion Matrix ===")
    print(pd.DataFrame(cm, index=labels, columns=labels))
    print()
    return cm


def top_confusions(cm: np.ndarray, labels, top_n=10):
    n = len(labels)
    confusions = []
    for i in range(n):
        for j in range(n):
            if i != j:
                confusions.append((cm[i, j], labels[i], labels[j]))
    confusions.sort(reverse=True, key=lambda x: x[0])
    return confusions[:top_n]


def analyze_leakage(df: pd.DataFrame):
    print("=== Target Leakage Analysis ===")
    if "priority_original" in df.columns:
        for orig_label, std_label in [("urgent", "High"), ("routine", "Medium"), ("cosmetic", "Low")]:
            subset = df[df["priority"] == std_label]
            if len(subset) == 0:
                continue
            contains_keyword = subset["complaint"].astype(str).str.lower().str.contains(orig_label)
            print(
                f"{std_label}: {contains_keyword.sum()}/{len(subset)} complaints contain '{orig_label}' word "
                f"({contains_keyword.mean():.2%})"
            )
    else:
        print("priority_original column not found; cannot inspect original label words.")
    print()


def check_duplicates(df: pd.DataFrame, X_train, X_test):
    print("=== Duplicate / Near-Duplicate Check ===")
    duplicate_rows = df.duplicated().sum()
    print(f"Exact duplicate rows in full dataset: {duplicate_rows}")
    if "complaint_proc" in df.columns:
        near_dup_count = df["complaint_proc"].duplicated().sum()
        print(f"Near-duplicate complaints after preprocessing: {near_dup_count}")
    train_texts = set(X_train)
    test_texts = set(X_test)
    overlap = len(train_texts & test_texts)
    print(f"Exact complaint text overlap between train/test: {overlap}")
    print()


def print_metrics(y_true, y_pred, labels, title):
    print(f"=== {title} Metrics ===")
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))
    print(f"Accuracy: {accuracy_score(y_true, y_pred):.4f}")
    print(f"Macro F1: {f1_score(y_true, y_pred, average='macro', zero_division=0):.4f}")
    print(f"Weighted F1: {f1_score(y_true, y_pred, average='weighted', zero_division=0):.4f}")
    print()


def train_baseline(X_train, X_test, y_train, y_test, labels, model_name):
    tfidf = TfidfVectorizer(max_features=10000)
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)

    clf = LogisticRegression(max_iter=1000, class_weight="balanced", solver="saga")
    clf.fit(X_train_tfidf, y_train)
    y_pred = clf.predict(X_test_tfidf)

    print(f"Baseline {model_name} results")
    print_metrics(y_test, y_pred, labels, model_name)
    return tfidf, clf, y_pred


def tune_pipeline(X_train, y_train, X_test, y_test, labels, model_name):
    print(f"=== Tuning {model_name} pipeline ===")
    pipeline = None
    from sklearn.pipeline import Pipeline

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", LogisticRegression(max_iter=1000, solver="saga", class_weight="balanced")),
        ]
    )

    param_grid = {
        "tfidf__ngram_range": [(1, 1), (1, 2)],
        "tfidf__min_df": [1, 2, 3],
        "tfidf__max_df": [0.9, 0.95, 1.0],
        "clf__C": [0.1, 1.0, 10.0],
    }

    search = GridSearchCV(
        pipeline,
        param_grid,
        cv=3,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=0,
    )
    search.fit(X_train, y_train)

    print(f"Best params for {model_name}: {search.best_params_}")
    best_pipeline = search.best_estimator_
    y_pred = best_pipeline.predict(X_test)
    print_metrics(y_test, y_pred, labels, f"Tuned {model_name}")
    return best_pipeline, y_pred, search.best_params_


def identify_confusions(y_true, y_pred, labels, title, top_n=10):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    top = top_confusions(cm, labels, top_n)
    print(f"=== Top {top_n} confusions for {title} ===")
    for count, true_label, pred_label in top:
        print(f"{count} examples: {true_label} → {pred_label}")
    print()
    return cm


def main():
    data_path = ROOT / "ml" / "dataset" / "cleaned_hotel_maintenance_dataset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned dataset not found: {data_path}")

    df = load_data(data_path)
    inspect_distribution(df)
    analyze_leakage(df)

    X_train, X_test, y_cat_train, y_cat_test, y_prio_train, y_prio_test = split_data(df)
    check_duplicates(df, X_train, X_test)

    category_labels = sorted(df["category"].unique())
    priority_labels = sorted(df["priority"].unique())

    print("--- Baseline Evaluation ---")
    baseline_tfidf_cat, baseline_cat_clf, y_cat_pred = train_baseline(
        X_train, X_test, y_cat_train, y_cat_test, category_labels, "Category"
    )
    baseline_tfidf_prio, baseline_prio_clf, y_prio_pred = train_baseline(
        X_train, X_test, y_prio_train, y_prio_test, priority_labels, "Priority"
    )

    compute_confusion(y_cat_test, y_cat_pred, category_labels, "Category")
    compute_confusion(y_prio_test, y_prio_pred, priority_labels, "Priority")
    identify_confusions(y_cat_test, y_cat_pred, category_labels, "Category")
    identify_confusions(y_prio_test, y_prio_pred, priority_labels, "Priority")

    print("--- Tune Category Model ---")
    tuned_category_pipeline, y_cat_pred_tuned, best_cat_params = tune_pipeline(
        X_train, y_cat_train, X_test, y_cat_test, category_labels, "Category"
    )
    print("--- Tune Priority Model ---")
    tuned_priority_pipeline, y_prio_pred_tuned, best_prio_params = tune_pipeline(
        X_train, y_prio_train, X_test, y_prio_test, priority_labels, "Priority"
    )

    print("=== Old vs New Summary ===")
    print("Category baseline accuracy:", accuracy_score(y_cat_test, y_cat_pred))
    print("Category tuned accuracy:", accuracy_score(y_cat_test, y_cat_pred_tuned))
    print("Priority baseline accuracy:", accuracy_score(y_prio_test, y_prio_pred))
    print("Priority tuned accuracy:", accuracy_score(y_prio_test, y_prio_pred_tuned))
    print()
    print("Category best params:", best_cat_params)
    print("Priority best params:", best_prio_params)

    # Optionally save best models
    out_dir = ROOT / "ml" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(tuned_category_pipeline, out_dir / "category_tuned_pipeline.pkl")
    joblib.dump(tuned_priority_pipeline, out_dir / "priority_tuned_pipeline.pkl")
    print(f"Saved tuned pipelines to {out_dir}")


if __name__ == "__main__":
    main()
