# 🚀 Multi-Agent Lead Intelligence System

An AI-powered lead intelligence platform that automatically researches companies, extracts contact information, and generates personalized outreach messages using a multi-agent pipeline. Designed to effortlessly scale using asynchronous processing.

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│              React + Vite Frontend              │
│         (Pulse Intelligence UI Design)          │
└────────────────────┬────────────────────────────┘
                     │ Axios HTTP
┌────────────────────▼────────────────────────────┐
│              FastAPI Backend                     │
│                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  │
│  │Researcher│→ │Contact Finder│→ │ Outreach  │  │
│  │  Agent   │  │    Agent     │  │  Writer   │  │
│  └──────────┘  └──────────────┘  └───────────┘  │
│       ↓              ↓                ↓          │
│   DuckDuckGo    4-Step Multi      Groq LLM      │
│   + Scraping    Source Search     (Llama 3.3)    │
└──────────────────────────────────────────────────┘
```

## ✨ Core Features

- **Researcher Agent** 🕵️‍♂️ — intelligently searches the web, scrapes multiple highly-relevant sources, and builds deeply curated profiles via LLM.
- **Contact Finder Agent** 📞 — A highly optimized 4-step discovery strategy: 
  1. Deep regex scanning on site
  2. Targeted DDG "contact info" domain sweeping
  3. Context-aware `/contact` page parsing
  4. LLM-based fallback extraction
- **Outreach Writer Agent** ✍️ — Generates engaging and natural WhatsApp-style outreach messages personalized to the extracted data.
- **Parallel Batch Processing** ⚡ — Blazing fast ingestion of multiple companies concurrently mapped via `asyncio.gather`.
- **Excel Batch Upload** 📊 — Directly upload `.xlsx` spreadsheets to process 10s-100s of companies seamlessly.
- **Pulse Intelligence UI** 🎨 — A premium dashboard design with rounded glass forms, dynamic red-to-coral gradients, pill-shaped accents, expand/collapse cells, and loading pulse states.

## 🛠 Tech Stack

| Layer | Technologies |
|-------|-----------|
| **Frontend** | React, Vite, Axios, Lucide React, Premium CSS (Inter font) |
| **Backend** | Python, FastAPI, Uvicorn, Asyncio |
| **LLM & AI** | Groq API (`llama-3.3-70b-versatile`) |
| **Scraping logic** | Requests, BeautifulSoup4, DuckDuckGo Search (`ddgs`) |

## 🚀 Getting Started Locally

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create environment configuration
cp .env.example .env
# Important: Open .env and add your Groq API key (GROQ_API_KEY)

uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install

# Create environment configuration
cp .env.example .env

npm run dev
```

## 🌍 Environment Variables Setup

### Backend (`backend/.env`)
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Frontend (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | API health and system check |
| `POST` | `/process-company` | Triggers agents on a single company string point |
| `POST` | `/process-excel` | Triggers parallel agents on multiple companies from `.xlsx` upload |

## 🚢 Deployment Guide

### Deploying the Backend (Render / Railway)
1. In Render, select **New Web Service** and upload this repository.
2. Select the **Root Directory** as `backend`.
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Make sure to add the `GROQ_API_KEY` to the service environment variables!
5. Note the generated service URL (e.g. `https://lead-intel.onrender.com`).

### Deploying the Frontend (Vercel)
1. In Vercel, select **Add New Project** and connect the repository.
2. Select the **Root Directory** as `frontend`.
3. Under Environment Variables, add `VITE_API_BASE_URL` with the URL from your deployed backend above.
4. Hit **Deploy** and the Pulse design system UI will compile!
