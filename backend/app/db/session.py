from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import re

# Force psycopg dialect for Python 3.14 compatibility
# Replace any postgresql URL variant with postgresql+psycopg
database_url = settings.DATABASE_URL
database_url = re.sub(r'^postgresql(\+psycopg2)?://', 'postgresql+psycopg://', database_url)

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
