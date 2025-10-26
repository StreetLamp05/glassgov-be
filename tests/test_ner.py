from src.app.services.ner_service import analyze

def test_food_access():
    out = analyze("Our neighborhood is a food desert with no grocery store.")
    assert out["category"] in ("food_access","health")
    assert "food_access" in out["tags"]

def test_crime():
    out = analyze("Two shootings and a car break-in last week near Market St.")
    assert out["category"] == "crime" or out["confidence"] >= 0.7
