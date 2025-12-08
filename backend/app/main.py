"""
FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import projects, scans, vulnerabilities, dashboard, reports, policies, tokens, upload, auth, file_history, notifications, ai
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Checkov Dashboard API",
    description="REST API for Checkov Security Scanning Dashboard",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
app.include_router(upload.router, prefix="/api/scans", tags=["upload"])
app.include_router(vulnerabilities.router, prefix="/api/vulnerabilities", tags=["vulnerabilities"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(policies.router, tags=["policies"])
app.include_router(tokens.router, tags=["tokens"])
app.include_router(file_history.router, prefix="/api/history", tags=["file-history"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])
app.include_router(ai.router, prefix="/api", tags=["ai"])

@app.get("/")
async def root():
    return {
        "message": "Checkov Dashboard API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
