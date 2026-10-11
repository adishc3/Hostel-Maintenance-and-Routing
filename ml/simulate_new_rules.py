import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "ml" / "dataset"
current_fp = DATA_DIR / "dataset_hostel.csv"
diag_fp = DATA_DIR / "electrical_diagnosis_report.csv"
out_fp = DATA_DIR / "electrical_simulation_results.csv"

def contains_any(text, kws):
    t = (text or "").lower()
    return any(k in t for k in kws)

def electrical_failure_context(text, equipment_list):
    # context words indicating electrical failure
    failure_ctx = [
        "not working", "not turning on", "won't turn on", "won't turn off", "stopped", "stops",
        "failed", "failure", "fault", "malfunction", "not spinning", "no power", "power cut",
        "no electricity", "flicker", "flickering", "dim", "won't turn", "tripped", "short", "sparking",
    ]
    t = (text or "").lower()
    # check explicit phrases
    if contains_any(t, failure_ctx):
        # ensure the equipment word is nearby - simple heuristic: equipment appears anywhere
        if contains_any(t, equipment_list):
            return True
    # check combined shorter patterns like "light flickering" or "lamp not working"
    for eq in equipment_list:
        for f in ["not working", "stopped", "flicker", "flickering", "dim", "won't turn"]:
            if f in t and eq in t:
                return True
    return False

def simulate(text):
    # Strong electrical indicators
    strong = [
        "electricity", "electrical", "electric", "wiring", "circuit", "voltage",
        "power outage", "power supply", "power socket", "electrical socket", "outlet", "socket",
        "switch", "fuse", "breaker", "circuit breaker", "short circuit", "shock", "power failure",
    ]

    equipment = [
        "light", "lamp", "fan", "exhaust fan", "ceiling fan", "appliance", "refrigerator", "fridge",
        "microwave", "oven", "washing machine", "dryer", "water heater", "heating element", "motor", "pump",
    ]

    text = (text or "").lower()

    # explicit phrase list (keep current explicit phrases)
    electrical_phrases = [
        "does not turn on", "doesn't turn on", "not turning on", "not turning off", "won't turn on", "won't turn off",
        "no electricity", "power outage", "socket", "outlet", "plug", "wiring", "switch", "electrical shock", "electric shock",
        "flicker", "flickering", "light flicker", "light is flickering", "light is not", "light not", "light doesn't",
        "fan not", "fan stopped", "fan doesn't", "extraction fan", "exhaust fan", "electric fault", "electrical fault",
    ]

    # 1) strong indicator present (and not clearly AV/HVAC-only)
    if contains_any(text, strong):
        return "Electrical"

    # 2) explicit phrase match
    if contains_any(text, electrical_phrases):
        # but avoid AV/IT false positives: require power/socket context for wifi/tv/pos/projector
        av_terms = ["wifi", "tv", "projector", "cctv", "pos", "background music", "remote", "speaker", "audio"]
        if contains_any(text, av_terms):
            # if also has strong indicator or 'socket'/'plug'/'power' nearby then Electrical
            if contains_any(text, ["socket", "plug", "power", "outlet", "no electricity"]):
                return "Electrical"
            else:
                return "General"
        return "Electrical"

    # 3) contextual equipment + failure context
    if electrical_failure_context(text, equipment):
        return "Electrical"

    # 4) appliance specific checks: appliance + malfunction words
    if contains_any(text, ["appliance", "not working", "malfunction", "broken", "stopped"]) and contains_any(text, ["refrigerator","fridge","microwave","oven","washing machine","dryer","coffee machine","ice machine"]):
        return "Electrical"

    # otherwise keep current class (simulate no change)
    return None

def main():
    cur = pd.read_csv(current_fp)
    diag = pd.read_csv(diag_fp)
    diag_ids = diag['id'].astype(int).tolist()

    rows = []
    for _, r in cur[cur['id'].isin(diag_ids)].iterrows():
        sim = simulate(r['complaint'])
        rows.append({
            'id': r['id'],
            'complaint': r['complaint'],
            'current': r['hostel_category'],
            'simulated': sim,
            'original_category': r['category']
        })

    out = pd.DataFrame(rows)
    out.to_csv(out_fp, index=False)
    print('Wrote simulation', out_fp)
    # show 20 examples where simulated Electrical but current not Electrical
    changed = out[(out['simulated']=='Electrical') & (out['current']!='Electrical')]
    print('\nExamples that WOULD change to Electrical (first 20):')
    print(changed.head(20).to_string(index=False))

if __name__ == '__main__':
    main()
