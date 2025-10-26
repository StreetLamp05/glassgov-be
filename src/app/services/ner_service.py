from typing import Dict, List


'''
categories:
food_access
crime 
housing
zoning
transport
budget
health
'''


KEYWORD_TO_CATEGORY = {
    "grocery": "food_access",
    "food": "food_access",
    "produce": "food_access",
    "road": "road_safety",
    "pothole": "road_safety",
    "accident": "road_safety",
    "crime": "crime",
    "shooting": "crime",
    "rent": "housing",
    "zoning": "zoning",
    "bus": "transport",
    "train": "transport",
    "budget": "budget",
    "clinic": "health",
    "hospital": "health",
    "urgent care": "health",
}

def analyze(text: str) -> Dict:
    text_lc = text.lower()
    for kw, cat in KEYWORD_TO_CATEGORY.items():
        if kw in text_lc:
            return {
                "category": cat,
                "tags": list({kw}),
                "entities": [],  # fill later
            }
    return {"category": "health", "tags": [], "entities": []}  # safe default for mvp

