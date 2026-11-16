import os
from dotenv import load_dotenv
load_dotenv()
# ---------- MySQL (Data Warehouse) ----------
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DB = os.getenv("MYSQL_DB", "laboratorio_etl")
# ---------- MongoDB (Staging) ----------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "laboratorio_etl")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "raw")
# ---------- API pública: Dragon Ball API ----------
API_NOMBRE = "Dragon Ball API" # sale en la respuesta de /extraer
API_URL = "https://dragonball-api.com/api/characters" # endpoint de UNA sola entidad
ID_CAMPO = "id" # campo que trae el ID original
ID_TIPO = int # los ids de esta API son enteros