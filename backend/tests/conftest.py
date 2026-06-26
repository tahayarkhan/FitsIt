import pytest
from helpers import make_item


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
