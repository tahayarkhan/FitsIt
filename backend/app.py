import os
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

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

    ext = _safe_extension(file.filename, file.content_type)
    uid = str(uuid4())
    folder = CATEGORY_TO_FOLDER[cat]
    storage_path = f"{folder}/{uid}{ext}"

    bucket = supabase.storage.from_(BUCKET_NAME)
    file_options = {}
    if file.content_type:
        file_options["content-type"] = file.content_type

    try:
        bucket.upload(
            storage_path,
            file_bytes,
            file_options=file_options or None,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Storage upload failed: {exc!s}") from exc

    image_url = bucket.get_public_url(storage_path)

    row = {
        "image_url": image_url,
        "storage_path": storage_path,
        "category": cat,
        "primary_colour": None,
        "secondary_colour": None,
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
