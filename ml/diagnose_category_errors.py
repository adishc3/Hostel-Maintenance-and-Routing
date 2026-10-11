import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.text_preprocessing import preprocess_complaint_text
from ml.train_optimized import SOURCE_DATA, STOPWORDS_FILE, classify_hostel_category


RANDOM_STATE = 42
EXAMPLES = {
    "no electricity / power socket": "There is no electricity in my room and the power socket is not working.",
    "broken door hinge": "The door hinge is broken and the door is difficult to close.",
    "ceiling fan": "The ceiling fan is not working properly.",
    "hallway light / socket": "The hallway light and electrical socket are not working.",
}
NEGATION_TERMS = frozenset(
    {"no", "not", "nor", "without", "don", "don't", "doesn", "doesn't", "isn", "isn't"}
)


def _load_data() -> tuple[pd.DataFrame, frozenset[str]]:
    stop_words = frozenset(
        word.strip()
        for word in STOPWORDS_FILE.read_text(encoding="utf-8").splitlines()
        if word.strip()
    )
    df = pd.read_csv(SOURCE_DATA).dropna(subset=["complaint", "priority"]).copy()
    df["complaint"] = df["complaint"].astype(str)
    df["complaint_norm"] = df["complaint"].str.strip().str.lower()
    df = df.drop_duplicates(subset=["complaint_norm"], keep="first").copy()
    df["hostel_category"] = df["complaint"].map(classify_hostel_category)
    df["processed"] = df["complaint"].map(
        lambda text: preprocess_complaint_text(text, stop_words)
    )
    df = df[df["processed"].str.len() > 0].copy()
    return df, stop_words


def _fit_word_model(
    texts: pd.Series,
    labels: pd.Series,
    *,
    class_weight: str | None = None,
    ngram_range: tuple[int, int] = (1, 2),
    min_df: int = 2,
    max_features: int = 5000,
) -> tuple[TfidfVectorizer, LogisticRegression]:
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=0.95,
        sublinear_tf=True,
    )
    features = vectorizer.fit_transform(texts)
    model = LogisticRegression(
        max_iter=1000, random_state=RANDOM_STATE, class_weight=class_weight
    )
    model.fit(features, labels)
    return vectorizer, model


def _metric_record(
    labels: list[str],
    truth: pd.Series,
    predictions: np.ndarray,
) -> dict:
    report = classification_report(
        truth,
        predictions,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    matrix = confusion_matrix(truth, predictions, labels=labels)
    return {
        "accuracy": report["accuracy"],
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "per_class": {
            label: {
                "precision": report[label]["precision"],
                "recall": report[label]["recall"],
                "f1": report[label]["f1-score"],
                "support": int(report[label]["support"]),
            }
            for label in labels
        },
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_labels": labels,
    }


def _fit_predictor(
    candidate: str,
    train_df: pd.DataFrame,
    stop_words: frozenset[str],
):
    if candidate == "baseline_word_tfidf":
        vectorizer, model = _fit_word_model(
            train_df["processed"], train_df["hostel_category"]
        )
        return lambda texts: model.predict(vectorizer.transform(texts))

    if candidate == "balanced_word_tfidf":
        vectorizer, model = _fit_word_model(
            train_df["processed"],
            train_df["hostel_category"],
            class_weight="balanced",
        )
        return lambda texts: model.predict(vectorizer.transform(texts))

    if candidate == "expanded_word_ngrams":
        vectorizer, model = _fit_word_model(
            train_df["processed"],
            train_df["hostel_category"],
            ngram_range=(1, 3),
            min_df=1,
            max_features=10000,
        )
        return lambda texts: model.predict(vectorizer.transform(texts))

    if candidate == "negation_preserving_word_tfidf":
        keep_negation = stop_words - NEGATION_TERMS
        train_text = train_df["complaint"].map(
            lambda text: preprocess_complaint_text(text, keep_negation)
        )
        vectorizer, model = _fit_word_model(train_text, train_df["hostel_category"])
        return lambda texts: model.predict(
            vectorizer.transform(
                texts.map(lambda text: preprocess_complaint_text(text, keep_negation))
            )
        )

    word_vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=2,
        max_features=30000,
        sublinear_tf=True,
    )
    features = FeatureUnion(
        [("word", word_vectorizer), ("char", char_vectorizer)]
    ).fit(train_df["processed"], train_df["hostel_category"])
    model = LogisticRegression(
        max_iter=1000, random_state=RANDOM_STATE, class_weight="balanced"
    )
    model.fit(features.transform(train_df["processed"]), train_df["hostel_category"])
    return lambda texts: model.predict(features.transform(texts))


def run_experiment(report_path: Path) -> dict:
    df, stop_words = _load_data()
    development_df, final_test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=df["hostel_category"],
    )
    fit_df, validation_df = train_test_split(
        development_df,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=development_df["hostel_category"],
    )
    labels = sorted(df["hostel_category"].unique())
    candidates = (
        "baseline_word_tfidf",
        "balanced_word_tfidf",
        "expanded_word_ngrams",
        "negation_preserving_word_tfidf",
        "word_char_tfidf_balanced",
    )
    validation_results = {}
    for candidate in candidates:
        predict = _fit_predictor(candidate, fit_df, stop_words)
        predictions = predict(validation_df["processed"])
        validation_results[candidate] = _metric_record(
            labels, validation_df["hostel_category"], predictions
        )
        validation_results[candidate]["probe_predictions"] = {
            name: str(
                predict(
                    pd.Series(
                        [
                            preprocess_complaint_text(text, stop_words - NEGATION_TERMS)
                            if candidate == "negation_preserving_word_tfidf"
                            else preprocess_complaint_text(text, stop_words)
                        ]
                    )
                )[0]
            )
            for name, text in EXAMPLES.items()
        }

    selected_candidate = max(
        candidates,
        key=lambda candidate: (
            validation_results[candidate]["macro_f1"],
            min(
                validation_results[candidate]["per_class"]["Electrical"]["recall"],
                validation_results[candidate]["per_class"]["Structural"]["recall"],
            ),
        ),
    )

    final_results = {}
    for candidate in ("baseline_word_tfidf", selected_candidate):
        predict = _fit_predictor(candidate, development_df, stop_words)
        predictions = predict(final_test_df["processed"])
        final_results[candidate] = _metric_record(
            labels, final_test_df["hostel_category"], predictions
        )

    report = {
        "purpose": "Diagnose category errors and compare alternatives without replacing production artifacts.",
        "scikit_learn_version": sklearn.__version__,
        "random_state": RANDOM_STATE,
        "dataset_rows_after_exact_deduplication": int(len(df)),
        "class_counts": {
            str(label): int(count)
            for label, count in df["hostel_category"].value_counts().sort_index().items()
        },
        "split": {
            "development_rows": int(len(development_df)),
            "fit_rows": int(len(fit_df)),
            "validation_rows": int(len(validation_df)),
            "reserved_final_test_rows": int(len(final_test_df)),
            "development_validation": "stratified 80/20 within the original 80% development partition",
            "final_test": "the original stratified 20% partition, not used for model selection",
        },
        "preprocessing_facts": {
            "stopwords_removed": sorted(NEGATION_TERMS & stop_words),
            "socket_in_current_active_vocabulary": False,
            "source_category_to_rule_label": pd.crosstab(
                df["category"], df["hostel_category"]
            ).to_dict(),
            "term_counts_by_rule_label": {
                term: {
                    str(label): int(count)
                    for label, count in (
                        df.loc[
                            df["processed"].str.contains(
                                rf"\b{term}\w*\b", case=False, regex=True
                            ),
                            "hostel_category",
                        ]
                        .value_counts()
                        .items()
                    )
                }
                for term in ("electric", "power", "socket", "light", "fan", "hinge", "door")
            },
        },
        "validation_results": validation_results,
        "selected_candidate_by_validation": selected_candidate,
        "selection_rule": "Highest validation macro F1, tie-break by the higher of the minimum Electrical/Structural recall.",
        "reserved_final_test_results": final_results,
        "probe_examples": EXAMPLES,
        "production_artifacts_modified": False,
    }

    # Record the active vocabulary coverage for diagnosis without using test data.
    active_vocabulary = set(joblib.load(ROOT / "ml" / "models" / "tfidf.pkl").vocabulary_)
    report["preprocessing_facts"]["socket_in_current_active_vocabulary"] = (
        "socket" in active_vocabulary
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    output = ROOT / "ml" / "evaluation" / "category_error_experiments.json"
    results = run_experiment(output)
    print(json.dumps({
        "selected_candidate_by_validation": results["selected_candidate_by_validation"],
        "validation_results": {
            name: {
                "accuracy": result["accuracy"],
                "macro_f1": result["macro_f1"],
                "per_class": result["per_class"],
                "probe_predictions": result["probe_predictions"],
            }
            for name, result in results["validation_results"].items()
        },
        "reserved_final_test_results": {
            name: {
                "accuracy": result["accuracy"],
                "macro_f1": result["macro_f1"],
                "per_class": result["per_class"],
            }
            for name, result in results["reserved_final_test_results"].items()
        },
        "report": str(output),
    }, indent=2))
