# MealPlanner (28-day cycle) — GitHub Pages + Python API

This project gives you:
- A **28‑day (7x4)** meal template (Domingo → Sábado) that auto-fills any month (loops every 28 days).
- A **calendar view** for the real month.
- **Dishes + ingredients** so you can generate a **shopping list + estimated cost**.
- A simple **shared-password login** to allow only you + your partner to edit.

## 1) How the 7x4 template works
You fill a 28-day cycle (4 weeks). For any month:
- Day 1 uses cycle day 1
- Day 2 uses cycle day 2
- ...
- Day 29 loops back to cycle day 1, etc.

You can also set per-date overrides for special days.

## 2) Local run (recommended first)

### Backend (Python)
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt

# Set a password + secret:
export MEALPLANNER_PASSWORD="a-strong-shared-password"
export JWT_SECRET="another-secret-string"

uvicorn backend.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000

### Frontend
Open `frontend/index.html` in your browser (or run a simple static server):
```bash
cd frontend
python -m http.server 5500
```
Then open: http://localhost:5500

## 3) Deploy (simple)

### Frontend → GitHub Pages
- Put `frontend/` in a repo (or move it to `/docs`).
- Enable GitHub Pages for that folder.
- Edit `frontend/app.js` and set `API_BASE` to your backend URL.

### Backend → Render / Fly.io / Railway (anything that runs Python)
You need a real backend host (GitHub Pages is static).

**Render example**
- Build command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Env vars:
  - `MEALPLANNER_PASSWORD`
  - `JWT_SECRET`
  - `ALLOWED_ORIGINS` = `https://YOURNAME.github.io` (and your custom domain if you use one)

> IMPORTANT: SQLite is fine for local use. For deployment, use a persistent disk or switch to Postgres
by setting `DATABASE_URL` (e.g., a Supabase/Render Postgres URL).

## 4) API quick test
```bash
curl "http://localhost:8000/api/calendar?year=2025&month=12"
```

## 5) Notes on security
This is a **shared-password** solution (good enough for “only us can edit”).
If you want stronger security, swap auth to **Supabase Auth** or **GitHub OAuth** later.
