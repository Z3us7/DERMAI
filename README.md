# DermAI — Production Deployment Guide

Welcome to the DermAI full-stack repository! This application is a complete, end-to-end medical AI platform featuring a React frontend, a FastAPI backend, a PyTorch computer vision engine, and a LangChain RAG pipeline.

## 🌟 Architecture Overview

1. **Frontend:** React + Vite, styled with Tailwind CSS and Framer Motion. Deployed on **Vercel**.
2. **Backend:** Python + FastAPI. Deployed on **Render.com**.
3. **Database & Auth:** PostgreSQL and Row Level Security powered by **Supabase**.
4. **AI Engine (Vision):** Custom PyTorch EfficientNet-B3 model recognizing 121 skin conditions.
5. **AI Engine (LLM):** LangChain RAG pipeline with OpenAI GPT-4o-mini to generate patient-friendly clinical notes.

---

## 🚀 Live URLs

- **Frontend Application:** https://dermai-gilt.vercel.app/
- **Backend API (Swagger):** `https://dermai-backend-ugbd.onrender.com/docs`
- **Database:** Supabase Project Dashboard

---

## 🛠️ Deployment Configuration (For Maintainers)

### 1. Render.com (Backend)
The backend is hosted on a free Render Web Service. It requires the following specific configuration due to PyTorch's memory footprint:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:**
  - `PYTHON_VERSION`: `3.11.0` *(Required to prevent source-build OOM errors)*
  - `MODEL_PATH`: `backend/DermAI_Mega_Payload.pth` *(Points to the model checkpoint directory)*
  - `CORS_ALLOW_ORIGINS`: `["*"]` *(Update to your exact Vercel URL in production)*
  - `OPENAI_API_KEY`: `sk-...` *(Your OpenAI key. If omitted, the server safely falls back to a deterministic Mock LLM mode)*

### 2. Supabase (Database & Auth)
The database schema is fully automated via the `supabase_schema.sql` file. 
- To initialize or reset the database, copy the contents of `supabase_schema.sql` and run it in the Supabase SQL Editor.
- It handles creating the `profiles` table, the `scan_results` table, the `scan-images` storage bucket, and all necessary Row Level Security (RLS) policies.

### 3. Vercel (Frontend)
The frontend requires the following environment variables to connect to the backend and database:
- `VITE_API_URL`: `https://dermai-backend-ugbd.onrender.com`
- `VITE_SUPABASE_URL`: *(Your Supabase Project URL)*
- `VITE_SUPABASE_ANON_KEY`: *(Your Supabase Anon Key)*

*Important:* You must add your Vercel deployment URL to the Supabase Authentication **URL Configuration** whitelist, or logins will be blocked.

---

## 🤖 The LLM RAG Pipeline

This application uses a LangChain Retrieval-Augmented Generation (RAG) pipeline to explain complex medical predictions to patients at a 6th-grade reading level.

**Mock Mode Fallback:**
If you do not provide an `OPENAI_API_KEY` in the Render environment variables, the backend will gracefully fallback to a deterministic Mock Mode. You will see `[MOCK LLM RESPONSE]` in the UI. This is intentional and proves the pipeline architecture works safely even when API quotas are exhausted or keys are missing.

---

## 💻 Local Development

To run the backend locally:
```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

To run the frontend locally:
```powershell
cd frontend
npm install
npm run dev
```

### Code Quality Commands
- **Run Tests:** `pytest tests/ -v`
- **Run Linter:** `ruff check app/ tests/`
- **Format Code:** `black app/ tests/`
