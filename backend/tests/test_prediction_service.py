import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.services.prediction_service import (  # noqa: E402
    CATEGORY_LABELS,
    PRIORITY_LABELS,
    PredictionError,
    PredictionService,
)
from app.services.text_preprocessing import preprocess_complaint_text  # noqa: E402


EXTERNAL_COMPLAINTS = (
    "The bathroom tap in my room is leaking continuously.",
    "There is no electricity in my room and the power socket is not working.",
    "The wall in the corridor has a large crack.",
    "The WiFi connection in my room is very weak.",
    "Water is leaking from the ceiling and falling onto the floor.",
    "The ceiling fan is not working properly.",
    "The door hinge is broken and the door is difficult to close.",
    "The room furniture is damaged and needs replacement.",
)


class PredictionServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = PredictionService()

    def test_both_models_load_and_accept_shared_vectorized_input(self) -> None:
        stop_words = self.service._stop_words
        cleaned = preprocess_complaint_text(
            "The bathroom tap is leaking continuously.", stop_words
        )
        features = self.service._vectorizer.transform([cleaned])
        category = self.service._category_model.predict(features)[0]
        priority = self.service._priority_model.predict(features)[0]
        self.assertIn(category, CATEGORY_LABELS)
        self.assertIn(priority, PRIORITY_LABELS)

    def test_representative_complaints_use_expected_label_sets(self) -> None:
        examples = (
            "The hallway light and electrical socket are not working.",
            "Water is leaking from the bathroom tap.",
            "There is a large crack in the corridor wall.",
            "The WiFi network in my room is weak.",
        )
        results = [self.service.predict(text) for text in examples]
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertIn(result.category, CATEGORY_LABELS)
            self.assertIn(result.priority, PRIORITY_LABELS)
            self.assertGreaterEqual(result.category_confidence, 0.0)
            self.assertLessEqual(result.category_confidence, 1.0)
            self.assertGreaterEqual(result.priority_confidence, 0.0)
            self.assertLessEqual(result.priority_confidence, 1.0)

    def test_notebook_external_examples_are_predictable_without_assuming_correctness(self) -> None:
        predictions = [self.service.predict(text) for text in EXTERNAL_COMPLAINTS]
        self.assertEqual(len(predictions), 8)
        self.assertTrue(all(item.category in CATEGORY_LABELS for item in predictions))
        self.assertTrue(all(item.priority in PRIORITY_LABELS for item in predictions))

    def test_empty_and_invalid_complaints_fail_clearly(self) -> None:
        for text in ("", " \t "):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.service.predict(text)
        with self.assertRaises(ValueError):
            self.service.predict("12345 !!! and the")
        with self.assertRaises(TypeError):
            self.service.predict(None)

    def test_missing_artifact_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                PredictionService(models_dir=Path(directory))

    def test_prediction_failure_is_logged_and_raised(self) -> None:
        original_predict = self.service._category_model.predict
        self.service._category_model.predict = Mock(side_effect=RuntimeError("failed"))
        try:
            with self.assertLogs("app.services.prediction_service", level="ERROR"):
                with self.assertRaises(PredictionError):
                    self.service.predict("The bathroom tap is leaking.")
        finally:
            self.service._category_model.predict = original_predict


if __name__ == "__main__":
    unittest.main()
