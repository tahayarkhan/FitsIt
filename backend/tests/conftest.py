import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class MockSupabaseTable:
    def __init__(self, data):
        self.data = data
    
    def select(self, *_args, **_kwargs):
        return self
    
    def execute(self):
        return type("Result", (), {"data": self._data})()

class MockSupabase:
    def __init__(self, clothing_items):
        self.items = clothing_items
    
    def table(self, name):
        assert name == "clothing_items"
        return MockSupabaseTable(self._items)




def make_item(item_id: str, category: str, rgb: dict | None = None) -> dict:
    return {
        "id": item_id,
        "image_url": f"https://example.com/{item_id}.jpg",
        "category": category,
        "primary_colour": None,
        "dominant_rgb": rgb,
    }


@pytest.fixture
def sample_top():
    return make_item("top-1", "top", {"r": 200, "g": 50, "b": 50})

@pytest.fixture
def sample_bottom():
    return make_item("bottom-1", "bottom", {"r": 50, "g": 50, "b": 200})  

@pytest.fixture
def sample_shoes():
    return make_item("shoes-1", "shoes", {"r": 128, "g": 128, "b": 128})  

@pytest.fixture
def sample_outerwear():
    return make_item("outer-1", "outerwear", {"r": 0, "g": 0, "b": 0})


@pytest.fixture
def full_wardrobe(sample_top, sample_bottom, sample_shoes, sample_outerwear):
    return [sample_top, sample_bottom, sample_shoes, sample_outerwear]

