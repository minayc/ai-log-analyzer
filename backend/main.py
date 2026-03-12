import os
from pathlib import Path
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import create_engine, Column, Integer, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates




app = FastAPI()
templates = Jinja2Templates(directory="templates")


LOG_PATH = Path(os.getenv("LOG_PATH", "/logs/app.log"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/app.db")


if DATABASE_URL.startswith("sqlite:////"):
    db_file = DATABASE_URL.replace("sqlite:////", "/")
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)


Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),nullable=False)
    n = Column(Integer, nullable=False)
    model = Column(Text, nullable=False)
    log_tail = Column(Text, nullable=False)
    summary =  Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)



@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ollama-version")
async def ollama_version():
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{OLLAMA_BASE_URL}/api/version")
        r.raise_for_status()
        return r.json()


def tail_lines(file_path: Path, n: int = 30) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found at {file_path}")
    lines = file_path.read_text(errors="ignore").splitlines()
    return "\n".join(lines[-n:])

async def run_analysis_and_store(n: int) -> Analysis:
    try:
        log_text = tail_lines(LOG_PATH, n=n)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    prompt = (
        "You are a senior site reliability engineer.\n"
        "Analyze the following logs and respond EXACTLY in this structure:\n\n"
        "SUMMARY:\n"
        "One short paragraph.\n\n"
        "CAUSES:\n"
        "- bullet\n"
        "- bullet\n"
        "- bullet\n\n"
        "NEXT STEPS:\n"
        "- bullet\n"
        "- bullet\n"
        "- bullet\n\n"
        f"LOGS:\n{log_text}\n"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json()

    summary = data.get("response", "").strip()

    db = SessionLocal()
    try:
        row = Analysis(
            n=n,
            model=OLLAMA_MODEL,
            log_tail=log_text,
            summary=summary,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    finally:
        db.close()


@app.get("/analyze-latest")
async def analyze_latest(n: int = 30):
    row = await run_analysis_and_store(n)

    return {
        "id": row.id,
        "created_at": row.created_at,
        "n": row.n,
        "model": row.model,
        "summary": row.summary,
    }

@app.get("/history")
def history(limit: int=20):
    db = SessionLocal()
    try:
        rows = (
            db.query(Analysis)
            .order_by(Analysis.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "created_at": r.created_at,
                "n": r.n,
                "model": r.model,
                "summary": r.summary
            }
            for r in rows
        ]
    finally:
        db.close()


@app.get("/history/{analysis_id}")
def history_detail(analysis_id: int):
    db = SessionLocal()
    try:
        r = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Not found")
        return {
            "id": r.id,
            "created_at": r.created_at,
            "n": r.n,
            "model": r.model,
            "summary": r.summary,
            "log_tail": r.log_tail,
        }
    finally:
        db.close()


@app.get("/analyze-latest-pretty", response_class=PlainTextResponse)
async def analyze_latest_pretty(n: int = 30):
    row = await run_analysis_and_store(n)

    summary = row.summary.strip()

    return (
        f"\n"
        f"========================================\n"
        f"        LOG ANALYSIS #{row.id}\n"
        f"========================================\n\n"
        f"Model:   {row.model}\n"
        f"Created: {row.created_at}\n\n"
        f"{summary}\n\n"
        f"========================================\n"
    )

@app.get("/")
def ui_home(request: Request, limit: int = 20):
    db = SessionLocal()
    try:
        rows = (
            db.query(Analysis)
            .order_by(Analysis.id.desc())
            .limit(limit)
            .all()
        )
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "history": rows},
        )
    finally:
        db.close()


@app.get("/run")
async def ui_run(n: int= 30):
    row = await run_analysis_and_store(n)
    return RedirectResponse(url=f"/ui/history/{row.id}", status_code=302)


@app.get("/ui/history/{analysis_id}")
def ui_history_detail(request: Request, analysis_id: int):
    db = SessionLocal()
    try:
        r = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Not Found")
        return templates.TemplateResponse(
            "detail.html",
            {"request": request, "item": r},
        )
    finally:
        db.close()





