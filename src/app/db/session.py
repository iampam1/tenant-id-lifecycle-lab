from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.core.config import settings # Adjusted import path

# Create a SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True # Recommended for ensuring connections are live
    # connect_args={"check_same_thread": False} # Only needed for SQLite, not PostgreSQL
)

# Create a SessionLocal class, which will be used to create database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# You can also add a function here to initialize the database if needed,
# for example, to create all tables (though Alembic is preferred for this).
# def init_db():
#     from src.app.models.base import Base # Import Base from your models
#     Base.metadata.create_all(bind=engine)
