import os
from uuid import uuid4
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client


from color_extraction import ColorExtractor
from io import BytesIO

from services.outfit_generator import OutfitGenerator
from services.outfit_scorer import OutfitScorer


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in the environment.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

BUCKET_NAME = "clothing-images"

ALLOWED_CATEGORIES = frozenset({"top", "bottom", "shoes", "outerwear", "other"})

# Storage folders match scope (tops/, bottoms/, …); DB stores singular category values.
CATEGORY_TO_FOLDER = {
    "top": "tops",
    "bottom": "bottoms",
    "shoes": "shoes",
    "outerwear": "outerwear",
    "other": "other",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

ALLOWED_CONFIDENCE = frozenset({"high", "medium", "low"})

OUTFIT_SLOT_CATEGORIES = {
    "top": "top",
    "bottom": "bottom",
    "shoes": "shoes",
    "outerwear": "outerwear",
}


extractor = ColorExtractor()


def _origins() -> list[str]:
    raw = os.getenv("FRONTEND", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    return {"message": "FitsIt API"}


def _safe_extension(filename: str | None, content_type: str | None) -> str:
    if filename and "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_EXTENSIONS:
            return ext
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        if ct in mapping:
            return mapping[ct]
    return ".jpg"


@app.post("/upload-item")
async def upload_item(
    file: UploadFile = File(...),
    category: str = Form(...),
):
    cat = category.strip().lower()
    if cat not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(sorted(ALLOWED_CATEGORIES))}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")


    output = await asyncio.to_thread(extractor.process_upload, file_bytes)

    masked_bytes = output['masked_bytes']

    ext = ".jpg"
    uid = str(uuid4())
    folder = CATEGORY_TO_FOLDER[cat]
    storage_path = f"{folder}/{uid}{ext}"

    bucket = supabase.storage.from_(BUCKET_NAME)
    file_options = {"content-type": "image/jpeg"}


    try:
        bucket.upload(
            storage_path,
            masked_bytes,
            file_options=file_options or None,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Storage upload failed: {exc!s}") from exc

    image_url = bucket.get_public_url(storage_path)

    
    colours = output['colours']
    primary_colour = colours["primary_color"]
    dominant_rgb = colours["dominant_rgb"]


    row = {
        "image_url": image_url,
        "storage_path": storage_path,
        "category": cat,
        "primary_colour": primary_colour,
        "secondary_colour": None,
        "dominant_rgb": dominant_rgb,
    }

    try:
        result = supabase.table("clothing_items").insert(row).execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database insert failed: {exc!s}") from exc

    return {
        "message": "Item uploaded",
        "image_url": image_url,
        "storage_path": storage_path,
        "category": cat,
        "db_record": result.data,
    }


@app.get("/items")
async def get_items():
    result = supabase.table("clothing_items").select("*").execute()
    return {"items": result.data or []}


generator = OutfitGenerator(supabase)
scorer = OutfitScorer()


@app.get("/recommendations")

async def get_recommendations(top_n: int = 5, include_outerwear: bool = False):

    outfits = await asyncio.to_thread(generator.generate_outfits, include_outerwear)

    if not outfits:
        return {
            "recommendations": [],
            "total_generated": 0,
            "message": "Not enough items. Need at least 1 top, 1 bottom, and 1 pair of shoes."
        }
    
    scored = []

    for outfit in outfits:
        score_result = scorer.score_outfit(outfit)
        scored.append({
            "outfit": {
                "top": _slim_item(outfit["top"]),
                "bottom": _slim_item(outfit["bottom"]),
                "shoes": _slim_item(outfit["shoes"]),
                "outerwear": _slim_item(outfit.get("outerwear"))
            },
            **score_result
        })
    
    return {
        "recommendations": scored,
        "total_generated": len(scored),
        "message": None
    }
    


def _slim_item(item: dict | None) -> dict | None:
    if not item:
        return None
    return {
        "id": item.get("id"),
        "image_url": item.get("image_url"),
        "category": item.get("category")
    }


def _outfit_item_id(outfit: dict, clothing_type: str) -> str:
    item = outfit.get(clothing_type) 
    if not isinstance(item, dict):
        raise HTTPException(status_code=400, detail=f"Missing outfit.{clothing_type}.id")
    item_id = item.get("id")
    if not item_id:
        raise HTTPException(status_code=400, detail=f"Missing outfit.{clothing_type}.id")
    return item_id

def _optional_outfit_item_id(outfit: dict, slot: str) -> str | None:
    item = outfit.get(slot)
    if item is None:
        return None
    if not isinstance(item, dict):
        raise HTTPException(status_code=400, detail=f"Invalid outfit.{slot}")
    item_id = item.get("id")
    if not item_id:
        raise HTTPException(status_code=400, detail=f"Invalid outfit.{slot}")
    return item_id


@app.post("/wardrobe")
async def save_outfit(body: dict):
    outfit = body.get("outfit")

    if not isinstance(outfit, dict):
        raise HTTPException(status_code=400, detail="Missing or invalid outfit.")
    
    top_id = _outfit_item_id(outfit, "top")
    bottom_id = _outfit_item_id(outfit, "bottom")
    shoes_id = _outfit_item_id(outfit, "shoes")
    outerwear_id = _optional_outfit_item_id(outfit, "outerwear")

    score = body.get("score")

    if score is None:
        raise HTTPException(status_code=400, detail="Missing score.")

    components = body.get("components")

    if not isinstance(components, dict):
        raise HTTPException(status_code=400, detail="Missing or invalid components.")


    reasons = body.get("reasons")

    if not isinstance(reasons, list):
        raise HTTPException(status_code=400, detail="Missing or invalid reasons.")


    confidence = body.get("confidence")

    if confidence not in ALLOWED_CONFIDENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid confidence. Must be one of: {', '.join(sorted(ALLOWED_CONFIDENCE))}",
        )

    item_ids = [top_id, bottom_id, shoes_id]

    if outerwear_id:
        item_ids.append(outerwear_id)
    
    
    try:
        items_result = (
            supabase.table("clothing_items").select("id, category").in_("id", item_ids).execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database lookup failed: {exc!s}") from exc

    items_by_id = {row["id"]: row for row in (items_result.data or [])}

    if len(items_by_id) != len(item_ids):
        raise HTTPException(status_code=400, detail="One or more clothing items not found.")

    clothing_item_ids = {
        "top" : top_id, 
        "bottom" : bottom_id,
        "shoes" : shoes_id,
    }

    if outerwear_id:
        clothing_item_ids["outerwear"] = outerwear_id
    
    for type_of_item, item_id in clothing_item_ids.items():
        expected = OUTFIT_SLOT_CATEGORIES[type_of_item]
        if items_by_id[item_id]["category"] != expected:
            raise HTTPException(
                status_code=400,
                detail=f"Item {item_id} is not a {expected}.",
            )
        
    duplicate_query = (
        supabase.table("wardrobe").select("id").eq("top_id", top_id).eq("bottom_id", bottom_id).eq("shoes_id", shoes_id)
    )

    if outerwear_id:
        duplicate_query = duplicate_query.eq("outerwear_id", outerwear_id)
    else:
        duplicate_query = duplicate_query.is_("outerwear_id", "null")
    

    try:
        existing = duplicate_query.execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database lookup failed: {exc!s}") from exc
    
    if existing.data:
        raise HTTPException(status_code=409, detail="Outfit already saved")
    
    row = {
        "top_id": top_id,
        "bottom_id": bottom_id,
        "shoes_id": shoes_id, 
        "outerwear_id" : outerwear_id,
        "score": score, 
        "components" : components,
        "reasons" : reasons,
        "confidence" : confidence,
    }

    try:
        result = supabase.table("wardrobe").insert(row).execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database insert failed: {exc!s}") from exc
    
    if not result.data:
        raise HTTPException(status_code=502, detail="Database insert failed.")


    return result.data[0]



@app.get("/wardrobe")
async def get_items():
    result = supabase.table("wardrobe").select("*").execute()
    return {"outfits": result.data or []}