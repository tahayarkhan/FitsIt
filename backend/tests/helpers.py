class MockSupabaseTable:
    def __init__(self, data):
        self._data = data

    def select(self, *_args, **_kwargs):
        return self

    def execute(self):
        return type("Result", (), {"data": self._data})()


class MockSupabase:
    def __init__(self, clothing_items):
        self._items = clothing_items

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
