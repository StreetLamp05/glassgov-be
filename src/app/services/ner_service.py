from __future__ import annotations
from functools import lru_cache
import os, re
from typing import Dict, List, Tuple

import spacy

# env toggles
USE_ZERO_SHOT = os.getenv("ZERO_SHOT", "1") == "1" and os.getenv("LLM_MOCK", "1") != "1"

CANDIDATE_LABELS = [
    "food_access", "road_safety", "crime", "housing",
    "zoning", "transport", "budget", "health"
]

# ---------- RULES ----------
# regex → (label, weight)
RULES: List[Tuple[re.Pattern, str, float]] = [
    (re.compile(r"\b(food desert|grocery|produce|supermarket|fresh food|food bank)\b", re.I), "food_access", 0.85),
    (re.compile(r"\b(pothole|speeding|crosswalk|traffic light|unsafe road|collision|accident)\b", re.I), "road_safety", 0.80),
    (re.compile(r"\b(homicide|shooting|robbery|assault|crime|car break[- ]?in|theft)\b", re.I), "crime", 0.85),
    (re.compile(r"\b(rent hike|eviction|landlord|affordable housing|shelter|homeless encampment)\b", re.I), "housing", 0.80),
    (re.compile(r"\b(zoning|rezon(e|ing)|variance|land use|setback|upzone)\b", re.I), "zoning", 0.75),
    (re.compile(r"\b(bus|transit|metro|subway|train|station|bike lane|sidewalk)\b", re.I), "transport", 0.75),
    (re.compile(r"\b(budget|appropriation|bond measure|levy|tax|funding cut|funding increase)\b", re.I), "budget", 0.75),
    (re.compile(r"\b(clinic|hospital|urgent care|public health|mental health|overdose)\b", re.I), "health", 0.70),
]

# ---------- spaCy NER-lite ----------
@lru_cache(maxsize=1)
def _nlp():
    return spacy.load("en_core_web_sm")

ENT_KEYS = ("GPE","LOC","FAC","ORG","DATE","TIME","MONEY","CARDINAL")

def extract_entities(text: str) -> Dict[str, List[str]]:
    doc = _nlp()(text)
    ents: Dict[str, List[str]] = {}
    for ent in doc.ents:
        if ent.label_ in ENT_KEYS:
            ents.setdefault(ent.label_, []).append(ent.text)
    streets = re.findall(r"\b([A-Z][a-z]+ (St|Ave|Blvd|Rd|Road|Street|Avenue|Boulevard))\b", text)
    if streets:
        ents["STREET"] = list({s[0] for s in streets})
    return ents

# ---------- Zero-shot (multi-label) ----------
@lru_cache(maxsize=1)
def _zero_shot():
    if not USE_ZERO_SHOT:
        return None
    from transformers import pipeline
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def zero_shot_scores(text: str) -> Dict[str, float]:
    """
    Returns per-label score for all CANDIDATE_LABELS using multi_label=True.
    If disabled, returns {}.
    """
    z = _zero_shot()
    if not z:
        return {}
    out = z(text, CANDIDATE_LABELS, multi_label=True)  # returns sorted labels & scores
    labels = out["labels"]
    scores = out["scores"]
    return {label: float(score) for label, score in zip(labels, scores)}

# ---------- Rule scores (multi-label) ----------
def rule_scores(text: str) -> Dict[str, float]:
    best: Dict[str, float] = {}
    for rx, label, weight in RULES:
        if rx.search(text):
            best[label] = max(best.get(label, 0.0), weight)
    return best  # e.g., {"crime": 0.85, "transport": 0.75}

# ---------- Fusion ----------
def fuse_scores(rule_map: Dict[str, float], zs_map: Dict[str, float]) -> Dict[str, float]:
    """
    Simple, effective fusion: per label, take the max(rule_weight, zero_shot_score).
    This favors high-precision rules but still lets zero-shot add new labels.
    """
    fused = {l: s for l, s in zs_map.items()}
    for l, s in rule_map.items():
        fused[l] = max(fused.get(l, 0.0), s)
    # Ensure every candidate exists (optional)
    for l in CANDIDATE_LABELS:
        fused.setdefault(l, 0.0)
    return fused

# ---------- Public API ----------
def analyze(
    text: str,
    threshold: float = 0.50,   # labels at/above this are returned
    top_k: int = 3              # if none meet threshold, return top_k anyway
) -> Dict:
    """
    Multi-label analysis.
    Returns:
      {
        "primary_category": <top label>,
        "categories": [{"label":..., "score":...}, ...],   # sorted desc
        "tags": [...],
        "entities": {...}
      }
    """
    text = (text or "").strip()
    rmap = rule_scores(text)
    zmap = zero_shot_scores(text) if USE_ZERO_SHOT else {}
    fused = fuse_scores(rmap, zmap)

    # sort labels by score desc
    sorted_items = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)

    # pick labels >= threshold; else fallback to top_k
    picked = [(l, s) for l, s in sorted_items if s >= threshold]
    if not picked:
        picked = sorted_items[:top_k]

    primary_label, primary_score = picked[0] if picked else ("health", 0.5)

    ents = extract_entities(text)
    tags = {l for l, _ in picked}  # just the selected labels; add rule hits if you like
    # include any rule hits explicitly
    tags.update(rmap.keys())

    return {
        "primary_category": primary_label,
        "categories": [{"label": l, "score": round(float(s), 3)} for l, s in picked],
        "confidence": round(float(primary_score), 3),
        "tags": sorted(tags),
        "entities": ents,
        "debug": {
            "rule_scores": rmap if os.getenv("NER_DEBUG", "0") == "1" else None,
            "zero_shot_scores": zmap if os.getenv("NER_DEBUG", "0") == "1" else None,
        }
    }
