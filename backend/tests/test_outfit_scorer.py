from services.outfit_scorer import OutfitScorer


def make_outfit_item(rgb: dict| None) -> dict:
    return {
        "id": "item-1",
        "image_url": "https://example.com/x.jpg",
        "category": "top",
        "dominant_rgb": rgb,
    }


def test_insuffcient_color_data():
    
    scorer = OutfitScorer() 
    
    outfit = {
        "top" : make_outfit_item({"r": 255, "g": 0, "b": 0}),
        "bottom": make_outfit_item(None), 
        "shoes": make_outfit_item(None),
        "outerwear": None,
    }

    result = scorer.score_outfit(outfit)

    assert result["score"] == 0
    assert result["confidence"] == "low"
    assert "insufficient_color_data" in result["reasons"]


def test_skips_items_without_dominant_rgb():

    scorer = OutfitScorer()

    colors = scorer._extract_colors({
        "top" : make_outfit_item({"r": 255, "g": 0, "b": 0}),
        "bottom": make_outfit_item(None),
        "shoes": make_outfit_item({"r": 0, "g": 0, "b": 255}),
        "outerwear": None,
    })

    assert len(colors) == 2

def test_complementary_pair_detected():
    
    scorer = OutfitScorer()

    outfit = {
        "top": make_outfit_item({"r": 255, "g": 0, "b": 0}),
        "bottom": make_outfit_item({"r": 0, "g": 255, "b": 255}),
        "shoes": make_outfit_item({"r": 128, "g": 128, "b": 128}),
        "outerwear": None,
    }

    result = scorer.score_outfit(outfit)

    assert result["score"] > 0
    assert "complementary_pair" in result["reasons"]


