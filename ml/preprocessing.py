import re
from typing import List

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
except Exception:
    nltk = None


def _ensure_nltk_data():
    global nltk
    if nltk is None:
        import nltk as _n
        nltk = _n
    try:
        stopwords.words("english")
    except Exception:
        nltk.download("punkt")
        nltk.download("wordnet")
        nltk.download("omw-1.4")
        nltk.download("stopwords")


def preprocess_text(text: str) -> str:
    """Normalize and clean complaint text.

    Steps:
    - Lowercase
    - Remove non-alphanumeric characters
    - Tokenize
    - Remove stopwords
    - Lemmatize

    This function must be reused for training, evaluation, and production.
    """
    if not isinstance(text, str):
        return ""

    _ensure_nltk_data()
    lemmatizer = WordNetLemmatizer()
    stops = set(stopwords.words("english"))

    # Lowercase
    s = text.lower()

    # Replace non-alphanumeric (keep spaces)
    s = re.sub(r"[^a-z0-9\s]", " ", s)

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    # Tokenize using a regex to avoid heavy NLTK punkt dependency
    tokens: List[str] = re.findall(r"\b[a-z0-9]+\b", s)

    # Filter stopwords and short tokens
    tokens = [t for t in tokens if t not in stops and len(t) > 1]

    # Lemmatize
    tokens = [lemmatizer.lemmatize(t) for t in tokens]

    return " ".join(tokens)


if __name__ == "__main__":
    examples = [
        "The FAN isn't working!!!",
        "Urgent: The treadmill in the gym caught fire briefly due to a motor fault.",
    ]
    for e in examples:
        print(e, "->", preprocess_text(e))
