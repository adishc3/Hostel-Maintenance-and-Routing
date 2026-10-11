import logging
from dataclasses import dataclass
from pathlib import Path

import joblib

from .text_preprocessing import preprocess_complaint_text


logger = logging.getLogger(__name__)

CATEGORY_LABELS = frozenset({"Electrical", "Plumbing", "Structural", "General"})
PRIORITY_LABELS = frozenset({"High", "Medium", "Low"})


class PredictionError(RuntimeError):
    """Raised when a loaded model cannot produce a complaint prediction."""


@dataclass(frozen=True)
class PredictionResult:
    category: str
    priority: str
    category_confidence: float | None
    priority_confidence: float | None


class PredictionService:
    def __init__(
        self,
        models_dir: Path | None = None,
        stopwords_file: Path | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[3]
        self._models_dir = models_dir or project_root / "ml" / "models"
        resource_path = stopwords_file or (
            project_root / "ml" / "resources" / "nltk_english_stopwords.txt"
        )

        self._stop_words = frozenset(
            word.strip() for word in resource_path.read_text(encoding="utf-8").splitlines()
            if word.strip()
        )
        if not self._stop_words:
            raise ValueError(f"Stop-word resource is empty: {resource_path}")

        self._vectorizer = joblib.load(self._models_dir / "tfidf.pkl")
        self._category_model = joblib.load(self._models_dir / "category.pkl")
        self._priority_model = joblib.load(self._models_dir / "priority.pkl")

        category_classes = set(self._category_model.classes_)
        priority_classes = set(self._priority_model.classes_)
        if category_classes != CATEGORY_LABELS:
            raise ValueError(f"Unexpected category model labels: {sorted(category_classes)}")
        if priority_classes != PRIORITY_LABELS:
            raise ValueError(f"Unexpected priority model labels: {sorted(priority_classes)}")

    def predict(self, complaint_text: str) -> PredictionResult:
        if not isinstance(complaint_text, str):
            raise TypeError("Complaint description must be a string")
        if not complaint_text.strip():
            raise ValueError("Complaint description must not be empty")

        cleaned_text = preprocess_complaint_text(complaint_text, self._stop_words)
        if not cleaned_text:
            raise ValueError("Complaint description has no usable words")

        try:
            features = self._vectorizer.transform([cleaned_text])
            category = str(self._category_model.predict(features)[0])
            priority = str(self._priority_model.predict(features)[0])
            category_confidence = self._confidence(self._category_model, features)
            priority_confidence = self._confidence(self._priority_model, features)
        except Exception as exc:
            logger.exception("Complaint prediction failed")
            raise PredictionError("Unable to predict complaint category and priority") from exc

        return PredictionResult(
            category=category,
            priority=priority,
            category_confidence=category_confidence,
            priority_confidence=priority_confidence,
        )

    @staticmethod
    def _confidence(model: object, features: object) -> float | None:
        predict_proba = getattr(model, "predict_proba", None)
        if predict_proba is None:
            return None
        return float(max(predict_proba(features)[0]))
