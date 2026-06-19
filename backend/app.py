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


# @app.get("/recommendations")

# async def get_recommendations(top_n: int = 5, include_outerwear: bool = False):

#     outfits = await asyncio.to_thread(generator.generate_outfits, include_outerwear)

#     if not outfits:
#         return {
#             "recommendations": [],
#             "total_generated": 0,
#             "message": "Not enough items. Need at least 1 top, 1 bottom, and 1 pair of shoes."
#         }
    
#     scored = []

#     for outfit in outfits:
#         score_result = scorer.score_outfit(outfit)
#         scored.append({
#             "outfit": {
#                 "top": _slim_item(outfit["top"]),
#                 "bottom": _slim_item(outfit["bottom"]),
#                 "shoes": _slim_item(outfit["shoes"]),
#                 "outerwear": _slim_item(outfit.get("outerwear"))
#             },
#             **score_result
#         })
    
#     return {
#         "recommendations": scored,
#         "total_generated": len(scored),
#         "message": None
#     }
    


def _slim_item(item: dict | None) -> dict | None:
    if not item:
        return None
    return {
        "id": item.get("id"),
        "image_url": item.get("image_url"),
        "category": item.get("category")
    }