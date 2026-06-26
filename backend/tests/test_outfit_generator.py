from helpers import MockSupabase, make_item
from services.outfit_generator import OutfitGenerator


def test_empty_wardrobe_returns_empty_list():
    client = MockSupabase([])
    generator = OutfitGenerator(client)

    assert generator.generate_outfits() == []


def test_missing_category_returns_empty_list():
    items = [make_item("top1", "top")]

    generator = OutfitGenerator(MockSupabase(items))

    assert generator.generate_outfits() == []

def test_generates_cartesian_product(full_wardrobe, sample_top, sample_bottom, sample_shoes):
    items = [sample_top, sample_bottom, sample_shoes]

    generator = OutfitGenerator(MockSupabase(items))

    outfits = generator.generate_outfits()

    assert len(outfits) == 1
    assert outfits[0]["top"]["id"] == "top-1"
    assert outfits[0]["bottom"]["id"] == "bottom-1"
    assert outfits[0]["shoes"]["id"] == "shoes-1"
    assert outfits[0]["outerwear"] is None

def test_two_tops_two_outfits():
    items = [
        make_item("top-1", "top"),
        make_item("top-2", "top"),
        make_item("bottom-1", "bottom"),
        make_item("shoes-1", "shoes"),
    ]

    generator = OutfitGenerator(MockSupabase(items))

    outfits = generator.generate_outfits()

    assert len(outfits) == 2 

def test_include_outerwear_attaches_to_each_base(full_wardrobe):
    generator = OutfitGenerator(MockSupabase(full_wardrobe))
    outfits = generator.generate_outfits(include_outerwear=True)
    assert len(outfits) == 1
    assert outfits[0]["outerwear"]["id"] == "outer-1"

