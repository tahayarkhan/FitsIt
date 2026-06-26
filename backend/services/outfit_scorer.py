import statistics
from itertools import combinations

from utils.color_utils import (
    hue_distance_deg,
    is_neutral,
    lightness_contrast,
    rgb_to_lch,
)


class OutfitScorer:

    COMPLEMENTARY = (150, 180)
    ANALOGOUS = (0, 30)
    TRIADIC = (110, 130)

    def _extract_colors(self, outfit: dict) -> list[dict]:

        colors = []

        for key in ["top", "bottom", "shoes", "outerwear"]:
            item = outfit.get(key)
            if item and item.get("dominant_rgb"):
                colors.append(item["dominant_rgb"])
        return colors


    def _score_harmony(self, colors: list[dict]) -> dict:
        best_score = 0.0
        reasons: list[str] = []

        hues = [rgb_to_lch(color).lch_h for color in colors]

        for h1, h2 in combinations(hues, 2):
            distance = hue_distance_deg(h1, h2)
            pair_score, reason = self._harmony_pair_score(distance)
            if pair_score > best_score:
                best_score = pair_score
                reasons = [reason] if reason else []
            elif pair_score == best_score and reason and reason not in reasons:
                reasons.append(reason)

        return {"score": round(best_score, 1), "reasons": reasons}

    
    def _score_neutrality(self, colors:list[dict]) -> dict:
        chromas = [rgb_to_lch(color).lch_c for color in colors]
        neutral_count = sum(1 for color in colors if is_neutral(color))

        if neutral_count >= 1:
            return {"score": 10.0, "reasons": ["neutral_anchor"]}
        min_chroma = min(chromas)
        score = max(0.0, min(5.0, 5.0 * (1 - (min_chroma - 15.0) / 35.0)))
        return {"score": round(score, 1), "reasons": []}

    def _score_balance(self, colors: list[dict]) -> dict:
        chromas = [rgb_to_lch(color).lch_c for color in colors]

        if len(chromas) > 1:
            spread = statistics.pstdev(chromas) 
        else:
            spread = 0.0

        score = max(0.0, min(15.0, 15.0 * (1 - spread / 50.0)))

        if score >= 10:
            reasons = ["balanced_chroma"] 
        else:
            reasons = []
        return {"score": round(score, 1), "reasons": reasons}

    def _contrast_pair_score(self, diff: float) -> float:
        if 30 <= diff <= 50:
            return 30.0
        if 20 <= diff < 30 or 50 < diff <= 60:
            return 22.0
        if diff < 20:
            return max(0.0, min(15.0, diff / 20.0 * 15.0))
        return max(0.0, min(15.0, 15.0 - (diff - 60.0) * 0.375))
        

    def _score_contrast(self, colors: list[dict]) -> dict:
        best_score = 0.0
        for c1, c2 in combinations(colors, 2):
            diff = lightness_contrast(c1, c2)
            pair_score = self._contrast_pair_score(diff)
            best_score = max(best_score, pair_score)
        if best_score >= 22:
            reasons = ["good_lightness_contrast"] 
        else:
            reasons = []
        return {"score": round(best_score, 1), "reasons": reasons}

    def _distance_to_nearest_window(self, value: float, windows: list[tuple[float, float]]) -> float:
        distances: list[float] = []
        for lo, hi in windows:
            if lo <= value <= hi:
                return 0.0
            if value < lo:
                distances.append(lo - value)
            else:
                distances.append(value - hi)
        return min(distances)
    
    def _harmony_pair_score(self, distance: float) -> tuple[float, str | None]:

        lo, hi = self.COMPLEMENTARY
        if lo <= distance <= hi:
            return 45.0, "complementary_pair"

        lo, hi = self.TRIADIC
        if lo <= distance <= hi:
            return 40.0, "triadic_pair"

        lo, hi = self.ANALOGOUS
        if lo <= distance <= hi:
            return 35.0, "analogous_pair"
        
        gap = self._distance_to_nearest_window(distance, [self.ANALOGOUS, self.TRIADIC, self.COMPLEMENTARY])
        score = max(0.0, min(20.0, 20.0 * (1 - gap / 60.0)))
        return score, None
        

    def _score_harmony(self, colors: list[dict]) -> dict:
        
        best_score = 0.0
        reasons: list[str] = []

        hues = [rgb_to_lch(color).lch_h for color in colors]

        for h1, h2 in combinations(hues, 2):
            distance = hue_distance_deg(h1, h2)
            pair_score, reason = self._harmony_pair_score(distance)
            if pair_score > best_score:
                best_score = pair_score
                reasons = [reason] if reason else []
            elif pair_score == best_score and reason and reason not in reasons:
                reasons.append(reason)

        return {"score": round(best_score, 1), "reasons": reasons}

    
    def score_outfit(self, outfit: dict) -> dict:
        
        colors = self._extract_colors(outfit)

        if len(colors) < 2:
            return {
                "score": 0,
                "components": {},
                "reasons": ["insufficient_color_data"],
                "confidence": "low",
            }

        harmony = self._score_harmony(colors)
        contrast = self._score_contrast(colors)
        balance = self._score_balance(colors)
        neutrality = self._score_neutrality(colors)

        final_score = (
            0.45 * harmony["score"]
            + 0.30 * contrast["score"]
            + 0.15 * balance["score"]
            + 0.10 * neutrality["score"]
        )

        reasons = (
            harmony["reasons"]
            + contrast["reasons"]
            + balance["reasons"]
            + neutrality["reasons"]
        )


        return {
            "score": round(final_score, 1),
            "components": {
                "harmony": harmony["score"],
                "contrast": contrast["score"],
                "balance": balance["score"],
                "neutrality": neutrality["score"],
            },
            "reasons": reasons,
            "confidence" : "high" if len(colors) >= 3 else "medium",
        }




def main():
    
    import os

    from dotenv import load_dotenv
    from outfit_generator_test import OutfitGenerator
    from supabase import create_client

    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    Og = OutfitGenerator(supabase_client)

    outfits = Og.generate_outfits()


    Os  = OutfitScorer()

    for outfit in outfits:
        print(Os._extract_colors(outfit))
        print(Os.score_outfit(outfit))


if __name__ == "__main__":
    main()

        