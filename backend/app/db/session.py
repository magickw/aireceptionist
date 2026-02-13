from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Replace psycopg2 with psycopg in DATABASE_URL for Python 3.14 compatibility
database_url = settings.DATABASE_URL.replace('postgresql+psycopg2://', 'postgresql+psycopg://')

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
