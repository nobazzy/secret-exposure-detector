import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.api.endpoints.jobs import router as jobs_router
from backend.app.api.endpoints.batch_scans import router as batch_scans_router
from backend.app.db.database import init_db

app = FastAPI(
    title="Critical Secret Exposure Detector API",
    version="4.2.0",
    description="API para auditoria e detecção estática de segredos expostos em repositórios. Integrada com GitRepository Intelligence Indexer."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()
    try:
        from backend.app.db.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET status = 'COMPLETED' WHERE status = 'RUNNING'")
        cursor.execute("UPDATE batch_scans SET status = 'COMPLETED' WHERE status = 'RUNNING'")
        conn.commit()
        conn.close()
    except Exception:
        pass

app.include_router(jobs_router, prefix="/api")
app.include_router(batch_scans_router, prefix="/api")

STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_dashboard():
        return FileResponse(str(STATIC_DIR / "index.html"))

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8001, reload=True)
