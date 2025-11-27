from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI()


SERPAPI_KEY = os.getenv("SERPAPI_KEY")
FRONTEND = os.getenv("FRONTEND")
origins = [FRONTEND]

app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], )


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/pinterest")
async def search_pinterest(query: str, num: int = 2):
    url = "https://serpapi.com/search.json"

    params = {
        "engine":"google_images",
        "q": query,
        "num":num,
        "api_key": SERPAPI_KEY
    }

    resp = requests.get(url, params=params)

    data = resp.json()

    image_results = data.get("images_results", [])

    pinterest_images = []

    for item in image_results:
        source = item.get("source")
        original = item.get("original")

        if source == "Pinterest" and original:
            pinterest_images.append(original)


    return {"images": pinterest_images}