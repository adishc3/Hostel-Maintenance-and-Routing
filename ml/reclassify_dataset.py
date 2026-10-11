import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "ml" / "dataset"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ELECTRICAL_KEYWORDS = [
    "electr", "fan", "light", "flicker", "flickering", "socket", "outlet", "plug", "power", "wiring", "switch",
    "charger", "voltage", "short", "fuse", "circuit", "power outage", "no electricity", "dead",
    "tripped", "not working", "not turning on", "not turning off", "appliance", "motor", "heater",
]

PLUMBING_KEYWORDS = [
    "pipe", "tap", "faucet", "toilet", "shower", "drain", "leak", "leaking", "water", "sewage",
    "blocked", "flush", "overflow", "sink", "hot water", "overflowing", "clog",
]

STRUCTURAL_KEYWORDS = [
    "door", "window", "ceiling", "wall", "lock", "hinge", "crack", "tile", "floor", "railing",
    "balcony", "roof", "frame", "scratch", "chip", "tear", "fray", "frayed", "broken leg", "loose",
    "hanging", "crooked", "collapse", "collapsed"
]

# Heuristic: if multiple category keyword sets match, mark as General


def token_count_matches(text: str, keywords):
    t = text.lower()
    count = 0
    for kw in keywords:
        # count occurrences
        count += t.count(kw)
    return count


def classify_row(complaint: str, original_category: str) -> str:
    text = (complaint or "").lower()

    def contains_any(text, phrases):
        return any(p in text for p in phrases)

    it_av_terms = ["wifi", "projector", "tv", "computer", "cctv", "pos system", "pos", "remote", "speaker", "audio", "music system", "background music"]

    electrical_phrases = [
        "does not turn on", "doesn't turn on", "not turning on", "not turning off", "won't turn on", "won't turn off",
        "no electricity", "power outage", "socket", "outlet", "plug", "wiring", "switch", "electrical shock", "electric shock",
        "flicker", "flickering", "light flicker", "light is flickering", "light is not", "light not", "light doesn't",
        "fan not", "fan stopped", "fan doesn't", "extraction fan", "exhaust fan", "electric fault", "electrical fault",
        "tripped", "blown fuse", "short circuit", "shorted", "sparking", "shocked", "power cut", "no power",
    ]

    # Strong single-token electrical indicators (context-aware)
    electrical_strong = [
        "electricity", "electrical", "electric", "wiring", "circuit", "voltage",
        "power outage", "power supply", "power socket", "electrical socket", "outlet", "switch",
        "fuse", "breaker", "circuit breaker", "short circuit", "shock", "power failure",
    ]

    # Equipment nouns that need failure-context to be classified Electrical
    electrical_equipment = [
        "light", "lamp", "fan", "exhaust fan", "ceiling fan", "appliance", "refrigerator", "fridge",
        "microwave", "oven", "washing machine", "dryer", "water heater", "heating element", "motor", "pump",
    ]

    def electrical_failure_context(text, equipment_list):
        failure_ctx = [
            "not working", "not turning on", "stopped", "stops", "failed", "failure", "fault", "malfunction",
            "not spinning", "no power", "power cut", "no electricity", "flicker", "flickering", "dim", "tripped",
            "short", "sparking",
        ]
        t = text.lower()
        if any(f in t for f in failure_ctx) and any(e in t for e in equipment_list):
            return True
        for e in equipment_list:
            for f in ["not working", "stopped", "flicker", "flickering", "dim", "won't turn"]:
                if f in t and e in t:
                    return True
        return False

    plumbing_phrases = [
        "pipe burst", "burst pipe", "leak", "leaking", "water leaking", "blocked drain", "blocked", "block", "clog",
        "toilet is blocked", "toilet blocked", "toilet overflow", "toilet is overflowing", "toilet overflow",
        "drain is", "drain blocked", "drain", "bathtub drain", "drain is slow", "hot water", "no hot water", "low water pressure",
        "water pressure", "water supply", "water pooling", "water leak", "sink is blocked", "shampoo dispenser", "shampoo dispenser is",
    ]

    structural_phrases = [
        "broken", "broken leg", "broken off", "crack", "cracked", "chip", "chipped", "scratch", "scratched", "tear", "torn",
        "frayed", "loose", "hanging", "falling off", "wobbly", "wobbles", "stuck", "detached", "collapsed", "collapse",
        "hinge", "hinges", "door", "window", "tile", "tiles", "floor", "ceiling", "wall", "furniture", "bedside", "table", "chair",
    ]

    has_it_av = contains_any(text, it_av_terms)
    has_electrical_phrase = contains_any(text, electrical_phrases)
    has_electrical_strong = contains_any(text, electrical_strong)
    has_plumbing = contains_any(text, plumbing_phrases)
    has_structural = contains_any(text, structural_phrases)

    # 1) Strong electrical tokens -> Electrical (context-aware)
    if has_electrical_strong:
        return "Electrical"

    # 2) Explicit electrical phrases -> Electrical, but avoid AV/IT false positives
    if has_electrical_phrase:
        if has_it_av:
            if contains_any(text, ["socket", "plug", "power", "outlet", "no electricity"]):
                return "Electrical"
            else:
                return "General"
        return "Electrical"

    # 3) Contextual equipment + failure-context
    if electrical_failure_context(text, electrical_equipment):
        return "Electrical"

    # 4) Appliance-specific but require explicit failure context (do not classify on noun alone)
    appliance_nouns = ["appliance","refrigerator","fridge","microwave","oven","washing machine","dryer","coffee machine","ice machine","machine","motor","pump"]
    failure_terms = ["not working","stopped","fault","malfunction","won't turn on","power failure","electrical fault","motor failure","heating element failure","not turning on"]
    if contains_any(text, appliance_nouns) and contains_any(text, failure_terms):
        return "Electrical"

    # fallthrough to plumbing/structural/general
    if has_plumbing:
        return "Plumbing"
    if has_structural:
        return "Structural"
    return "General"

def reclassify(input_csv: Path, output_csv: Path, original_copy: Path):
    df = pd.read_csv(input_csv)
    # Save a copy of the original cleaned dataset
    df.to_csv(original_copy, index=False)

    df = df.copy()
    # Create hostel_category
    df["hostel_category"] = df.apply(lambda r: classify_row(r.get("complaint", ""), r.get("category", "")), axis=1)

    # Keep original priority as already standardized
    # Add processed complaint column using existing preprocess_text if available
    try:
        from ml.preprocessing import preprocess_text
        df["complaint_proc"] = df["complaint"].astype(str).apply(preprocess_text)
    except Exception:
        df["complaint_proc"] = df["complaint"].astype(str)

    # Remove exact duplicate complaint texts (based on raw complaint text trimmed)
    df["complaint_norm"] = df["complaint"].astype(str).str.strip().str.lower()
    before = len(df)
    df = df.drop_duplicates(subset=["complaint_norm"])  # exact duplicates removed
    after = len(df)

    # Save the hostel dataset
    df.to_csv(output_csv, index=False)

    print(f"Original rows: {before}, after removing exact duplicates: {after}")
    return df, before, after


if __name__ == "__main__":
    input_csv = ROOT / "hotel_maintenance_dataset.csv"
    output_csv = DATA_DIR / "dataset_hostel.csv"
    original_copy = DATA_DIR / "dataset_original.csv"
    df, before, after = reclassify(input_csv, output_csv, original_copy)
    # Print distribution
    print("Hostel category distribution:\n", df["hostel_category"].value_counts())
