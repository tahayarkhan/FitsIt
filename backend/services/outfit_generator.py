from typing import TypedDict
from itertools import product

class OutfitItem(TypedDict):
    id: str
    image_url: str
    category: str
    primary_colour: dict | None
    dominant_rgb: dict | None

class Outfit(TypedDict):
    top: OutfitItem
    bottom: OutfitItem
    shoes: OutfitItem
    outerwear: OutfitItem | None



class OutfitGenerator:
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def fetch_items_by_category(self) -> dict[str, list[OutfitItem]]:

        result = self.supabase.table("clothing_items").select("*").execute()

        grouped: dict[str, list[OutfitItem]] = {
            "top": [],
            "bottom": [],
            "shoes": [],
            "outerwear": [],
        }


        for item in result.data or []:
            category = item.get("category")
            if category in grouped:
                grouped[category].append(item)
        
        return grouped
    

    def generate_outfits(self, include_outerwear: bool = False) -> list[Outfit]:

        items = self.fetch_items_by_category()

        if not items["top"] or not items["bottom"] or not items["shoes"]:
            return []
        
        outfits: list[Outfit] = []


        for top, bottom, shoes in product(items["top"], items["bottom"], items["shoes"]):
            base_outfit: Outfit = {
                "top": top,
                "bottom": bottom,
                "shoes": shoes,
                "outerwear": None,
            }

            if include_outerwear and items["outerwear"]:
                for outer in items["outerwear"]:
                    outfits.append({**base_outfit, "outerwear": outer})
            else:
                outfits.append(base_outfit)
        return outfits
    



def main():
    import os
    from dotenv import load_dotenv
    from supabase import create_client
    from pprint import pprint


    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    Og = OutfitGenerator(supabase_client)


if __name__ == "__main__":
    main()
        
