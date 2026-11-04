from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import dashboard, loans, uploads

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Zaradera Recovery Unit — PDL Dashboard",
    description="Weekly loan-sheet ingestion, PDL segmentation, and loan-level history for the recovery unit.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploads.router)
app.include_router(dashboard.router)
app.include_router(loans.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
