from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, businesses, call_logs, appointments, analytics, integrations, twilio, voice, automation, customer_intelligence, knowledge_base, call_summaries, webhooks, calendar, sms, forecasting, email, chatbot, reports, sentiment, churn, voice_greetings, call_routing, ai_training, menu, business_types, orders, approvals
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
    expose_headers=["*"],
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
app.include_router(knowledge_base.router, prefix=f"{settings.API_V1_STR}/knowledge-base", tags=["knowledge-base"])
app.include_router(call_summaries.router, prefix=f"{settings.API_V1_STR}/call-summaries", tags=["call-summaries"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["webhooks"])
app.include_router(calendar.router, prefix=f"{settings.API_V1_STR}/calendar", tags=["calendar"])
app.include_router(sms.router, prefix=f"{settings.API_V1_STR}/sms", tags=["sms"])
app.include_router(forecasting.router, prefix=f"{settings.API_V1_STR}/forecasting", tags=["forecasting"])
app.include_router(email.router, prefix=f"{settings.API_V1_STR}/email", tags=["email"])
app.include_router(chatbot.router, prefix=f"{settings.API_V1_STR}/chatbot", tags=["chatbot"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])
app.include_router(sentiment.router, prefix=f"{settings.API_V1_STR}/sentiment", tags=["sentiment"])
app.include_router(churn.router, prefix=f"{settings.API_V1_STR}/churn", tags=["churn"])
app.include_router(voice_greetings.router, prefix=f"{settings.API_V1_STR}/voice-greetings", tags=["voice-greetings"])
app.include_router(call_routing.router, prefix=f"{settings.API_V1_STR}/call-routing", tags=["call-routing"])
app.include_router(ai_training.router, prefix=f"{settings.API_V1_STR}/ai-training", tags=["ai-training"])
app.include_router(menu.router, prefix=f"{settings.API_V1_STR}/menu", tags=["menu"])
app.include_router(orders.router, prefix=f"{settings.API_V1_STR}/orders", tags=["orders"])
app.include_router(approvals.router, prefix=f"{settings.API_V1_STR}/approvals", tags=["approvals"])
app.include_router(business_types.router, prefix=f"{settings.API_V1_STR}/businesses", tags=["business-types"])


@app.get("/health")
def health_check():
    return {"status": "healthy"}
