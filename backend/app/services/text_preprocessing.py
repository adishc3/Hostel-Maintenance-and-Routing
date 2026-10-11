import re


def preprocess_complaint_text(text: str, stop_words: frozenset[str]) -> str:
    if not isinstance(text, str):
        raise TypeError("Complaint text must be a string")

    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", " ", text)
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    words = [word for word in text.split() if word not in stop_words]
    return re.sub(r"\s+", " ", " ".join(words)).strip()
