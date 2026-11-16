from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import (
    MONGO_COLLECTION,
    MONGO_DB,
    MONGO_URI,
    MYSQL_DB,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)

# ---------- MySQL (SQLAlchemy) ----------
mysql_url = URL.create( # URL.create escapa bien contraseñas con caracteres especiales
    "mysql+mysqlconnector",
    username=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DB,
)
engine = create_engine(mysql_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    """Dependencia de FastAPI: abre una sesión por petición y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- MongoDB (PyMongo) ----------
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]

def get_mongo_collection():
    """Colección de staging donde vive la data cruda."""
    return mongo_db[MONGO_COLLECTION]