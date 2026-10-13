import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

# Configure engine
connect_args = {}
if settings.normalized_database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.normalized_database_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend.app import models
    Base.metadata.create_all(bind=engine)
    
    # Create default demo workspace if none exists
    db = SessionLocal()
    try:
        ws = db.query(models.Workspace).first()
        if not ws:
            default_ws = models.Workspace(
                id=str(uuid.uuid4()),
                name="Acme E-Commerce Retail",
                default_currency=settings.default_currency,
                created_at=datetime.utcnow()
            )
            db.add(default_ws)
            db.commit()
    finally:
        db.close()
