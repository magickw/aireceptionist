from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, businesses, call_logs, appointments, analytics, integrations, twilio, voice, automation, customer_intelligence, automation
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(businesses.router, prefix=f"{settings.API_V1_STR}/businesses", tags=["businesses"])
app.include_router(call_logs.router, prefix=f"{settings.API_V1_STR}/call-logs", tags=["call-logs"])
app.include_router(appointments.router, prefix=f"{settings.API_V1_STR}/appointments", tags=["appointments"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(integrations.router, prefix=f"{settings.API_V1_STR}/integrations", tags=["integrations"])
app.include_router(twilio.router, prefix=f"{settings.API_V1_STR}/twilio", tags=["twilio"])
app.include_router(voice.router, prefix=f"{settings.API_V1_STR}/voice", tags=["voice"])
app.include_router(automation.router, prefix=f"{settings.API_V1_STR}/automation", tags=["automation"])
app.include_router(customer_intelligence.router, prefix=f"{settings.API_V1_STR}/customer-intelligence", tags=["customer-intelligence"])
app.include_router(automation.router, prefix=f"{settings.API_V1_STR}/automation", tags=["automation"])


@app.get("/health")
def health_check():
    return {"status": "healthy"}
