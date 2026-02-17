from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
import re
import logging

logger = logging.getLogger(__name__)

# Force psycopg dialect for Python 3.14 compatibility
# Replace any postgresql URL variant with postgresql+psycopg
database_url = settings.DATABASE_URL
database_url = re.sub(r'^postgresql(\+psycopg2)?://', 'postgresql+psycopg://', database_url)

# Log database URL for debugging (hide password)
safe_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', database_url)
logger.info(f"Connecting to database: {safe_url}")

try:
    engine = create_engine(database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Test connection
    with engine.connect() as conn:
        logger.info("Database connection successful")
except SQLAlchemyError as e:
    logger.error(f"Database connection failed: {str(e)}")
    raise Exception(f"Database connection failed. Please check DATABASE_URL environment variable. Error: {str(e)}")
except Exception as e:
    logger.error(f"Unexpected database error: {str(e)}")
    raise Exception(f"Database initialization error: {str(e)}")
