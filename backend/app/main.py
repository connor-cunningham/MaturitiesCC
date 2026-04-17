from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import dashboard, loans, properties, owners, uploads, crm, scoring, search, exports

app = FastAPI(
    title="MaturitiesCC API",
    description="Loan Maturity Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"

app.include_router(dashboard.router, prefix=PREFIX)
app.include_router(loans.router, prefix=PREFIX)
app.include_router(properties.router, prefix=PREFIX)
app.include_router(owners.router, prefix=PREFIX)
app.include_router(uploads.router, prefix=PREFIX)
app.include_router(crm.router, prefix=PREFIX)
app.include_router(scoring.router, prefix=PREFIX)
app.include_router(search.router, prefix=PREFIX)
app.include_router(exports.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
