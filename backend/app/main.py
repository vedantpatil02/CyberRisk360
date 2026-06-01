from fastapi import FastAPI

from app.database import engine
from app.database import Base

from app.models import User

from app.api.users import router as user_router
from app.api.assets import router as asset_router
from app.api.risks import router as risk_router
from app.api.vulnerabilities import router as vulnerability_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CyberRisk360",
    version="1.0.0"
)

app.include_router(user_router)
from app.api.auth import router as auth_router
app.include_router(auth_router)
app.include_router(asset_router)
app.include_router(risk_router)
app.include_router(vulnerability_router)

@app.get("/")
def home():

    return {
        "message": "CyberRisk360 API Running"
    }
