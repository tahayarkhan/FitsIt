# FitsIt

FitsIt is a smart wardrobe application that helps you organize clothing and discover outfit combinations. Upload photos of your clothes, and the app uses computer vision to isolate garments, extract dominant colors, and generate scored outfit recommendations based on color harmony theory.

## Demo

**Coming soon.**

## Features

- **Clothing upload** — Add items by category (top, bottom, shoes, outerwear, other) with image upload.
- **Automatic segmentation** — SegFormer isolates clothing from the background in uploaded photos.
- **Color extraction** — Dominant colors are extracted from each garment for downstream matching.
- **Outfit generation** — Combines items from your wardrobe into complete outfits when you have at least one top, bottom, and pair of shoes.
- **Color harmony scoring** — Outfits are ranked using complementary, analogous, and triadic color relationships.
- **Recommendations & wardrobe** — Browse top-scored outfit suggestions and save favorites to your personal wardrobe.

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| Frontend | React 19, Vite, Tailwind CSS, Radix UI, Framer Motion |
| Backend | FastAPI, Python 3.11, Uvicorn |
| ML / Vision | PyTorch, Transformers (SegFormer), scikit-learn, Pillow |
| Database & Storage | Supabase (PostgreSQL, Storage) |
| Tooling | Docker, Docker Compose, GitHub Actions, Ruff, pytest |

## Project Structure

```
FitsIt/
├── backend/
│   ├── app.py                  # FastAPI application and routes
│   ├── color_extraction.py     # SegFormer-based segmentation and color analysis
│   ├── services/
│   │   ├── outfit_generator.py # Outfit combination logic
│   │   └── outfit_scorer.py    # Color harmony scoring
│   ├── supabase/migrations/    # Database schema migrations
│   └── tests/                  # Backend unit tests
├── frontend/
│   └── src/
│       ├── components/         # UI components (upload, items, recommendations, wardrobe)
│       └── services/           # API client
├── docker-compose.yaml
└── .github/workflows/ci.yml
```

## Prerequisites

- **Node.js** 20+
- **Python** 3.11+
- **Docker & Docker Compose** (optional, for containerized development)
- **Supabase project** with migrations applied and a `clothing-images` storage bucket

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/tahayarkhan/FitsIt.git
cd FitsIt
```

### 2. Configure environment variables

Create `backend/.env`:

```env
SUPABASE_URL=<your-supabase-project-url>
SUPABASE_SERVICE_KEY=<your-supabase-service-role-key>
FRONTEND=http://localhost:5173
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Set up the database

Apply Supabase migrations from `backend/supabase/migrations/` to your project (via the Supabase CLI or dashboard). Ensure a public storage bucket named `clothing-images` exists.

### 4. Run locally

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

> The backend downloads the SegFormer model on first startup. A machine with a GPU (CUDA or Apple MPS) is recommended; CPU inference is supported but slower.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### 5. Run with Docker Compose

From the project root:

```bash
docker compose up --build
```

This starts the backend on port `8000` and the frontend on port `5173`.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/upload-item` | Upload a clothing item (multipart: `file`, `category`) |
| `GET` | `/items` | List all clothing items |
| `GET` | `/recommendations` | Get scored outfit recommendations |
| `PATCH` | `/recommendations/{id}` | Like or unlike a recommendation |
| `GET` | `/wardrobe` | Get saved (liked) outfits |

Interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) when the backend is running.

## License

This project is not currently licensed for public use.
