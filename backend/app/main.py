from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router

app = FastAPI(
    title="NetOps Research Prototype API",
    description="Context-Aware Automated Network Incident Management System (CESO -> CADD -> MSVS)",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "NetOps Prototype Backend", "version": "0.1.0"}
