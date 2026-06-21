import os
from uuid import uuid4
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client


from color_extraction import ColorExtractor

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
generator = OutfitGenerator(supabase)
scorer = OutfitScorer()

RECOMMENDATION_SELECT = (
    "id, score, components, reasons, confidence, liked, "
    "top:clothing_items!top_id(id, image_url, category), "
    "bottom:clothing_items!bottom_id(id, image_url, category), "
    "shoes:clothing_items!shoes_id(id, image_url, category), "
    "outerwear:clothing_items!outerwear_id(id, image_url, category)"
)


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
        insert_result = supabase.table("clothing_items").insert(row).execute()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database insert failed: {exc!s}") from exc

    if not insert_result.data:
        raise HTTPException(status_code=502, detail="Database insert failed.")

    new_item = insert_result.data[0]

    tops = supabase.table("clothing_items").select("id").eq("category", "top").execute()
    bottoms = supabase.table("clothing_items").select("id").eq("category", "bottom").execute()
    shoes = supabase.table("clothing_items").select("id").eq("category", "shoes").execute()

    if (
        cat in ("top", "bottom", "shoes")
        and len(tops.data) >= 1
        and len(bottoms.data) >= 1
        and len(shoes.data) >= 1
    ):
        outfits = await asyncio.to_thread(generator.generate_outfits_for_item, new_item)

        for outfit in outfits:
            score_result = scorer.score_outfit(outfit)
            recommendation_row = {
                "top_id": outfit["top"]["id"],
                "bottom_id": outfit["bottom"]["id"],
                "shoes_id": outfit["shoes"]["id"],
                "outerwear_id": None,
                **score_result,
                "liked": False,
            }

            try:
                supabase.table("recommendations").insert(recommendation_row).execute()
            except Exception as exc:
                if "duplicate key" in str(exc).lower() or "unique" in str(exc).lower():
                    continue
                raise HTTPException(
                    status_code=502,
                    detail=f"Database insert failed: {exc!s}",
                ) from exc

    return {
        "message": "Item uploaded",
        "image_url": image_url,
        "storage_path": storage_path,
        "category": cat,
        "db_record": insert_result.data,
    }


@app.get("/items")
async def get_items():
    result = supabase.table("clothing_items").select("*").execute()
    return {"items": result.data or []}

@app.get("/recommendations")
async def get_recommendations(top_n: int = 5):
    try:
        result = (
            supabase.table("recommendations")
            .select(RECOMMENDATION_SELECT)
            .order("score", desc=True)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database lookup failed: {exc!s}") from exc

    rows = result.data or []
    recommendations = [_format_recommendation(row) for row in rows]

    return {
        "recommendations": recommendations,
        "total": len(recommendations),
    }


def _slim_item(item: dict | None) -> dict | None:
    if not item:
        return None
    return {
        "id": item["id"],
        "image_url": item.get("image_url"),
        "category": item.get("category"),
    }


def _format_recommendation(row: dict) -> dict:
    return {
        "id": row["id"],
        "outfit": {
            "top": _slim_item(row.get("top")),
            "bottom": _slim_item(row.get("bottom")),
            "shoes": _slim_item(row.get("shoes")),
            "outerwear": _slim_item(row.get("outerwear")),
        },
        "score": row["score"],
        "components": row["components"],
        "reasons": row["reasons"],
        "confidence": row["confidence"],
        "liked": row.get("liked", False),
    }



@app.get("/wardrobe")
async def get_wardrobe():
    result = supabase.table("recommendations").select("*").eq("liked", "true").execute()
    return {"outfits": result.data or []}