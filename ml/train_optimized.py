import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy
import pandas as pd
import scipy
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.text_preprocessing import preprocess_complaint_text


SOURCE_DATA = ROOT / "cleaned_hotel_maintenance_dataset.csv"
STOPWORDS_FILE = ROOT / "ml" / "resources" / "nltk_english_stopwords.txt"

PLUMBING_KEYWORDS = (
    "water leak", "water leaking", "water leakage", "leaking water",
    "water dripping", "pipe leak", "pipe burst", "water pipe", "plumbing",
    "tap", "faucet", "sink", "wash basin", "washbasin", "toilet",
    "toilet flush", "flush", "shower", "bathtub", "bath tub", "drain",
    "drainage", "sewage", "sewage smell", "water pressure", "water supply",
    "hot water", "cold water", "water heater", "water pooling",
    "blocked toilet", "blocked drain", "overflowing toilet",
)
ELECTRICAL_KEYWORDS = (
    "electricity", "electrical", "electric shock", "electric vehicle",
    "charging point", "charging station", "power outage", "power failure",
    "no power", "without power", "power supply", "power socket",
    "power outlet", "wiring", "wire", "socket", "outlet", "switch",
    "circuit", "circuit breaker", "breaker", "fuse", "voltage",
    "electrical cupboard", "burning smell", "light bulb",
    "light not working", "lights not working", "lighting", "flickering light",
    "flickering lights", "fluorescent", "lamp", "fan", "ceiling fan",
    "exhaust fan", "motor fault", "motor", "air conditioning",
    "air conditioner", "heating system", "heating element", "thermostat",
    "oven", "electric oven", "treadmill", "machine caught fire",
)
STRUCTURAL_KEYWORDS = (
    "wall", "walls", "ceiling", "roof", "floor", "flooring", "floor tile",
    "floor tiles", "tile", "tiles", "door frame", "window", "windows",
    "window frame", "crack", "cracked", "cracking", "broken wall",
    "structural", "building damage", "plaster", "paint peeling",
    "paint is peeling", "wallpaper peeling", "wallpaper", "ceiling damage",
    "roof damage", "hinge", "door hinge", "damaged flooring",
)


def classify_hostel_category(text: str) -> str:
    text = text.lower()
    if any(keyword in text for keyword in PLUMBING_KEYWORDS):
        return "Plumbing"
    if any(keyword in text for keyword in ELECTRICAL_KEYWORDS):
        return "Electrical"
    if any(keyword in text for keyword in STRUCTURAL_KEYWORDS):
        return "Structural"
    return "General"


def _metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_weighted": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "classification_report": classification_report(
            y_true, y_pred, output_dict=True, zero_division=0
        ),
    }


def train(models_dir: Path, report_path: Path) -> dict:
    if not SOURCE_DATA.is_file():
        raise FileNotFoundError(f"Training dataset not found: {SOURCE_DATA}")
    stop_words = frozenset(
        word.strip()
        for word in STOPWORDS_FILE.read_text(encoding="utf-8").splitlines()
        if word.strip()
    )
    if not stop_words:
        raise ValueError(f"Stop-word resource is empty: {STOPWORDS_FILE}")

    df = pd.read_csv(SOURCE_DATA).dropna(subset=["complaint", "priority"]).copy()
    df["complaint"] = df["complaint"].astype(str)
    df["complaint_norm"] = df["complaint"].str.strip().str.lower()
    duplicate_count = int(df["complaint_norm"].duplicated().sum())
    df = df.drop_duplicates(subset=["complaint_norm"], keep="first").copy()
    df["hostel_category"] = df["complaint"].map(classify_hostel_category)
    df["complaint_proc"] = df["complaint"].map(
        lambda text: preprocess_complaint_text(text, stop_words)
    )
    df = df[df["complaint_proc"].str.len() > 0].copy()

    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["hostel_category"],
    )
    if set(train_df["complaint_norm"]) & set(test_df["complaint_norm"]):
        raise RuntimeError("Exact complaint text overlaps between train and test splits")

    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    train_features = vectorizer.fit_transform(train_df["complaint_proc"])
    test_features = vectorizer.transform(test_df["complaint_proc"])

    category_model = LogisticRegression(max_iter=1000, random_state=42)
    category_model.fit(train_features, train_df["hostel_category"])
    category_predictions = category_model.predict(test_features)

    priority_model = LogisticRegression(max_iter=1000, random_state=42)
    priority_model.fit(train_features, train_df["priority"])
    priority_predictions = priority_model.predict(test_features)
    priority_urgent_cue_counts = {}
    for label, label_df in df.groupby("priority"):
        urgent_count = int(
            label_df["complaint"].str.contains(r"\burgent\b", case=False, regex=True).sum()
        )
        priority_urgent_cue_counts[str(label)] = {
            "rows": int(len(label_df)),
            "complaints_containing_urgent": urgent_count,
        }

    external_complaints = [
        "The bathroom tap in my room is leaking continuously.",
        "There is no electricity in my room and the power socket is not working.",
        "The wall in the corridor has a large crack.",
        "The WiFi connection in my room is very weak.",
        "Water is leaking from the ceiling and falling onto the floor.",
        "The ceiling fan is not working properly.",
        "The door hinge is broken and the door is difficult to close.",
        "The room furniture is damaged and needs replacement.",
    ]
    external_cleaned = [
        preprocess_complaint_text(text, stop_words) for text in external_complaints
    ]
    external_features = vectorizer.transform(external_cleaned)
    external_categories = category_model.predict(external_features)
    external_priorities = priority_model.predict(external_features)
    external_predictions = [
        {
            "complaint": complaint,
            "category": str(category),
            "priority": str(priority),
        }
        for complaint, category, priority in zip(
            external_complaints, external_categories, external_priorities
        )
    ]

    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, models_dir / "tfidf.pkl")
    joblib.dump(category_model, models_dir / "category.pkl")
    joblib.dump(priority_model, models_dir / "priority.pkl")

    category_metrics = _metrics(test_df["hostel_category"], category_predictions)
    priority_metrics = _metrics(test_df["priority"], priority_predictions)
    report = {
        "source_dataset": str(SOURCE_DATA.relative_to(ROOT)),
        "source_rows_after_cleaning": int(len(df)),
        "exact_duplicate_rows_removed": duplicate_count,
        "train_size": int(len(train_df)),
        "test_size": int(len(test_df)),
        "split": {"test_size": 0.2, "random_state": 42, "stratify": "hostel_category"},
        "tfidf_fit_scope": "training partition only",
        "vectorizer_parameters": {
            "max_features": 5000,
            "ngram_range": [1, 2],
            "min_df": 2,
            "max_df": 0.95,
            "sublinear_tf": True,
        },
        "scikit_learn_version": sklearn.__version__,
        "joblib_version": joblib.__version__,
        "numpy_version": numpy.__version__,
        "scipy_version": scipy.__version__,
        "category_labels": sorted(map(str, category_model.classes_)),
        "priority_labels": sorted(map(str, priority_model.classes_)),
        "priority_urgent_cue_counts": priority_urgent_cue_counts,
        "category_metrics": category_metrics,
        "priority_metrics": priority_metrics,
        "external_predictions": external_predictions,
        "evaluation_limitations": [
            "The notebook fitted TF-IDF before its train/test split, so its reported test metrics include vocabulary/IDF leakage.",
            "This retraining fits TF-IDF only on training data; it does not eliminate possible near-duplicate or source-label bias.",
            "Category targets are generated by the notebook's keyword-based category rules, so category scores measure agreement with those heuristic labels rather than independent human adjudication.",
            "The word 'urgent' occurs in every priority class in the deduplicated source data; priority performance may still reflect source-text conventions.",
            "Notebook priority labels (High/Medium/Low) are preserved as trained labels.",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (report_path.parent / "category_report.json").write_text(
        json.dumps(category_metrics["classification_report"], indent=2), encoding="utf-8"
    )
    (report_path.parent / "priority_report.json").write_text(
        json.dumps(priority_metrics["classification_report"], indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and export the notebook-selected models.")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "ml" / "models")
    parser.add_argument(
        "--report-path",
        type=Path,
        default=ROOT / "ml" / "evaluation" / "optimized_model_report.json",
    )
    args = parser.parse_args()
    report = train(args.models_dir, args.report_path)
    print(json.dumps({
        "train_size": report["train_size"],
        "test_size": report["test_size"],
        "category_metrics": report["category_metrics"],
        "priority_metrics": report["priority_metrics"],
        "external_predictions": report["external_predictions"],
    }, indent=2))


if __name__ == "__main__":
    main()
