from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from src.api.webhook import router as webhook_router
from src.api.health import router as health_router
from src.api.agent import router as agent_router
from src.api.admin import router as admin_router
from src.api.gdpr import router as gdpr_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting Meetech Lead Qualification Bot...")
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Meetech Lead Qualification Bot",
    description="AI-powered WhatsApp chatbot for lead qualification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/v1", tags=["Health"])
app.include_router(webhook_router, prefix="/v1", tags=["Webhook"])
app.include_router(agent_router, prefix="/v1", tags=["Agent"])
app.include_router(admin_router, prefix="/v1", tags=["Admin"])
app.include_router(gdpr_router, prefix="/v1", tags=["GDPR"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
