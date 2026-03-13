import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from app.api.v1.endpoints import auth, businesses, call_logs, appointments, analytics, integrations, twilio, voice, automation, customer_intelligence, knowledge_base, call_summaries, webhooks, calendar, sms, forecasting, email, chatbot, reports, sentiment, churn, voice_greetings, call_routing, ai_training, menu, business_types, orders, approvals, business_templates, multimodal, diagnostics, payments, customer_360, revenue_analytics, smart_scheduling, builtin_calendar, campaigns, voice_personas, portal, dashboard_ws, calendly
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestLoggingMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.rate_limiter import limiter
from app.db.session import engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Register global exception handlers
register_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    """Ensure required tables and columns exist on startup."""
    try:
        with engine.connect() as conn:
            # 1. Ensure refresh_tokens table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'refresh_tokens'
                )
            """))
            table_exists = result.scalar()

            if not table_exists:
                print("[Startup] Creating refresh_tokens table...")
                conn.execute(text("""
                    CREATE TABLE refresh_tokens (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        token_hash VARCHAR(64) UNIQUE NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        revoked BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text("""
                    CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id)
                """))
                conn.execute(text("""
                    CREATE UNIQUE INDEX ix_refresh_tokens_token_hash ON refresh_tokens(token_hash)
                """))
                conn.commit()
                print("[Startup] refresh_tokens table created successfully")

            # 2. Ensure account lockout columns exist in users table
            # Check for failed_login_attempts
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'failed_login_attempts'
                )
            """))
            if not result.scalar():
                print("[Startup] Adding failed_login_attempts column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
                conn.commit()

            # Check for locked_until
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'locked_until'
                )
            """))
            if not result.scalar():
                print("[Startup] Adding locked_until column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP"))
                conn.commit()

            # E5: Ensure campaigns and campaign_calls tables exist
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'campaigns'
                )
            """))
            if not result.scalar():
                print("[Startup] Creating campaigns table...")
                conn.execute(text("""
                    CREATE TABLE campaigns (
                        id SERIAL PRIMARY KEY,
                        business_id INTEGER NOT NULL REFERENCES businesses(id),
                        name VARCHAR(255) NOT NULL,
                        campaign_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) DEFAULT 'draft',
                        briefing TEXT,
                        target_criteria JSON,
                        schedule JSON,
                        max_concurrent_calls INTEGER DEFAULT 3,
                        max_retries INTEGER DEFAULT 2,
                        total_targets INTEGER DEFAULT 0,
                        calls_made INTEGER DEFAULT 0,
                        calls_answered INTEGER DEFAULT 0,
                        calls_successful INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """))
                conn.execute(text("CREATE INDEX ix_campaigns_business_id ON campaigns(business_id)"))
                
                print("[Startup] Creating campaign_calls table...")
                conn.execute(text("""
                    CREATE TABLE campaign_calls (
                        id SERIAL PRIMARY KEY,
                        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                        customer_id INTEGER NOT NULL REFERENCES customers(id),
                        call_session_id VARCHAR(100) REFERENCES call_sessions(id),
                        status VARCHAR(20) DEFAULT 'pending',
                        attempt_number INTEGER DEFAULT 1,
                        outcome VARCHAR(50),
                        outcome_details TEXT,
                        call_duration_seconds INTEGER,
                        scheduled_at TIMESTAMP,
                        called_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text("CREATE INDEX ix_campaign_calls_campaign_id ON campaign_calls(campaign_id)"))
                conn.commit()
                print("[Startup] Campaigns tables created successfully")

            # Clean up stale refresh tokens
            try:
                result = conn.execute(text("""
                    DELETE FROM refresh_tokens
                    WHERE revoked = TRUE OR expires_at < NOW() - INTERVAL '7 days'
                """))
                conn.commit()
                deleted = result.rowcount
                if deleted:
                    logger.info("[Startup] Cleaned up %d stale refresh tokens", deleted)
            except Exception as e:
                logger.warning("[Startup] Token cleanup skipped: %s", e)
    except Exception as e:
        print(f"[Startup] Error checking/creating refresh_tokens table: {e}")

    # E5: Start the campaign scheduler
    try:
        from app.services.scheduler import start_scheduler
        start_scheduler()
        print("[Startup] Campaign scheduler started")
    except Exception as e:
        print(f"[Startup] Scheduler start failed (non-fatal): {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Dispose database connection pool on shutdown."""
    try:
        from app.services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
    try:
        engine.dispose()
        logger.info("[Shutdown] Database connection pool disposed")
    except Exception as e:
        logger.error("[Shutdown] Error disposing connection pool: %s", e)

# Rate limiting
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )

# CORS origins - explicit list required when allow_credentials=True
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://receptium.vercel.app",
    "https://receptium.onrender.com",
]
# Allow additional origins via environment variable (comma-separated)
extra_origins = os.getenv("CORS_ORIGINS", "")
if extra_origins:
    cors_origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Length", "X-Request-Id"],
)

# Request logging middleware (after CORS so preflight is handled first)
app.add_middleware(RequestLoggingMiddleware)

# Security headers on all responses
app.add_middleware(SecurityHeadersMiddleware)

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
app.include_router(business_templates.router, prefix=f"{settings.API_V1_STR}/admin/templates", tags=["admin-templates"])
app.include_router(multimodal.router, prefix=f"{settings.API_V1_STR}/multimodal", tags=["multimodal"])
app.include_router(diagnostics.router, prefix=f"{settings.API_V1_STR}", tags=["diagnostics"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])
app.include_router(customer_360.router, prefix=f"{settings.API_V1_STR}/customers", tags=["customers"])
app.include_router(revenue_analytics.router, prefix=f"{settings.API_V1_STR}/revenue", tags=["revenue"])
app.include_router(smart_scheduling.router, prefix=f"{settings.API_V1_STR}/smart-scheduling", tags=["smart-scheduling"])
app.include_router(builtin_calendar.router, prefix=f"{settings.API_V1_STR}/calendar/builtin", tags=["builtin-calendar"])
app.include_router(campaigns.router, prefix=f"{settings.API_V1_STR}/campaigns", tags=["campaigns"])
app.include_router(voice_personas.router, prefix=f"{settings.API_V1_STR}/voice-personas", tags=["voice-personas"])
app.include_router(portal.router, prefix=f"{settings.API_V1_STR}/portal", tags=["portal"])
app.include_router(dashboard_ws.router, prefix=f"{settings.API_V1_STR}", tags=["dashboard-ws"])
app.include_router(calendly.router, prefix=f"{settings.API_V1_STR}/calendly", tags=["calendly"])


@app.get("/health")
def health_check():
    """Health check endpoint to verify backend is working"""
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return JSONResponse(
                status_code=200,
                content={
                    "status": "healthy",
                    "database": "connected",
                    "api_version": "1.0.0"
                },
            )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
            },
        )
