from dataclasses import dataclass

import colour
import numpy as np


@dataclass(frozen=True)
class LabColor:
    lab_l: float
    lab_a: float
    lab_b: float


@dataclass(frozen=True)
class LCHColor:
    lch_l: float
    lch_c: float
    lch_h: float


def _rgb_array(rgb: dict) -> np.ndarray:
    return np.array([rgb["r"], rgb["g"], rgb["b"]], dtype=float) / 255.0


def _rgb_to_lab_array(rgb: dict) -> np.ndarray:
    return colour.XYZ_to_Lab(colour.sRGB_to_XYZ(_rgb_array(rgb)))


def rgb_to_lab(rgb: dict) -> LabColor:
    lab = _rgb_to_lab_array(rgb)
    return LabColor(lab_l=float(lab[0]), lab_a=float(lab[1]), lab_b=float(lab[2]))


def rgb_to_lch(rgb: dict) -> LCHColor:
    lch = colour.Lab_to_LCHab(_rgb_to_lab_array(rgb))
    return LCHColor(lch_l=float(lch[0]), lch_c=float(lch[1]), lch_h=float(lch[2]))


def hue_distance_deg(h1: float, h2: float) -> float:
    diff = abs(h1 - h2) % 360
    return min(diff, 360 - diff)


def delta_e(rgb1: dict, rgb2: dict) -> float:
    lab1 = _rgb_to_lab_array(rgb1)
    lab2 = _rgb_to_lab_array(rgb2)
    return float(colour.difference.delta_E_CIE2000(lab1, lab2))


def lightness_contrast(rgb1: dict, rgb2: dict) -> float:
    lab1 = rgb_to_lab(rgb1)
    lab2 = rgb_to_lab(rgb2)
    return abs(lab1.lab_l - lab2.lab_l)


def is_neutral(rgb: dict, chroma_threshold: float = 15) -> bool:
    lch = rgb_to_lch(rgb)
    return lch.lch_c < chroma_threshold
