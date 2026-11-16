import re
import requests
import pandas as pd
from sqlalchemy.dialects.mysql import insert as mysql_insert
from ..config import ID_TIPO
from ..database import Base, engine, get_mongo_collection
from ..models.entidad_sql import Entidad
from datetime import datetime
from pymongo import UpdateOne
from ..config import API_URL, ID_CAMPO
from ..database import get_mongo_collection
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import Base, engine, get_mongo_collection
from ..models.entidad_sql import Entidad

LOTE = 20 # personajes por página del listado

def descargar_registros(cantidad: int) -> list[dict]:
    """Dragon Ball API: listado paginado (items + links.next) y detalle de cada personaje."""
    sesion = requests.Session() # reutiliza la conexión entre peticiones

    # 1) Listado paginado: de aquí solo se necesita el ID de cada personaje
    resumen: list[dict] = []
    url: str | None = f"{API_URL}?limit={LOTE}"
    
    while url and len(resumen) < cantidad:
        respuesta = sesion.get(url, timeout=15)
        respuesta.raise_for_status()
        cuerpo = respuesta.json()
        resumen.extend(cuerpo["items"])
        url = cuerpo["links"].get("next") or None # "" en la última página

    # 2) Detalle de cada personaje (trae originPlanet y transformations)
    registros: list[dict] = []
    for item in resumen[:cantidad]:
        detalle = sesion.get(f"{API_URL}/{item[ID_CAMPO]}", timeout=15)
        detalle.raise_for_status()
        registros.append(detalle.json())

    return registros

def extraer_registros(cantidad: int) -> dict:
    """E del ETL: guarda en Mongo la data cruda sin duplicar.
    El _id del documento es el ID ORIGINAL de la API (PK natural), no un ObjectId.
    """
    # Un dict por ID: si la API repitiera un objeto, se cuenta una sola vez
    unicos = {r[ID_CAMPO]: r for r in descargar_registros(cantidad)}
    coleccion = get_mongo_collection()
    ids = list(unicos.keys())

    ya_existentes = coleccion.count_documents({"_id": {"$in": ids}})
    ahora = datetime.now() # fecha de extracción (hora local)

    operaciones = []
    for id_original, registro in unicos.items():
        documento = {k: v for k, v in registro.items() if k != ID_CAMPO}
        operaciones.append(
            UpdateOne(
                {"_id": id_original},
                {"$set": documento, "$setOnInsert": {"extraido_en": ahora}},
                upsert=True,
            )
        )

    if operaciones:
        coleccion.bulk_write(operaciones, ordered=False)

    return {"nuevos": len(ids) - ya_existentes, "ya_existentes": ya_existentes}

def reset_sistema(db: Session) -> dict:
    """C: vacía Mongo (delete_many) y MySQL (TRUNCATE, no DROP)."""
    Base.metadata.create_all(bind=engine) # resiliencia: si la tabla no existe, la crea
    filas = db.query(Entidad).count()
    db.execute(text(f"TRUNCATE TABLE {Entidad.__tablename__}"))
    db.commit()
    docs = get_mongo_collection().delete_many({}).deleted_count
    return {"mongo_docs_eliminados": docs, "mysql_rows_eliminadas": filas}

def _leer_mongo() -> list[dict]:
    """E: todos los documentos crudos de la colección raw."""
    return list(get_mongo_collection().find({}))

# ZONA ADAPTABLE (Dragon Ball) ---------------------------------------------------
# columna del DataFrame aplanado -> columna de la tabla SQL
MAPEO_COLUMNAS = {
    "_id": "id_personaje",
    "name": "nombre",
    "race": "raza",
    "gender": "genero",
    "affiliation": "afiliacion",
    "ki": "ki_base",  # se convierte a número en _limpiar
    "maxKi": "ki_maximo",
    "originPlanet_name": "planeta_origen",
    "originPlanet_isDestroyed": "planeta_destruido",
    "total_transformaciones": "total_transformaciones",  # derivada
    "extraido_en": "fecha_extraccion",  # derivada (la agrega /extraer)
}
COLUMNAS_TEXTO = ["nombre", "raza", "genero", "afiliacion", "ki_maximo", "planeta_origen"]
COLUMNAS_NUMERICAS = ["total_transformaciones"]
COLUMNAS_FECHA = ["fecha_extraccion"]
# ---------------------------------------------------------------------------------


def _aplanar(documentos: list[dict]) -> pd.DataFrame:
    """T (1): aplana el JSON anidado, deriva columnas y elimina las irrelevantes."""
    plano = pd.json_normalize(documentos, sep="_")

    # Derivada: cuántas transformaciones tiene (0 si no tiene lista)
    transformaciones = plano.get("transformations", pd.Series([None] * len(plano)))
    plano["total_transformaciones"] = transformaciones.apply(
        lambda lista: len(lista) if isinstance(lista, list) else 0
    )

    # Seleccionar y renombrar. reindex crea la columna vacía si un personaje no trae el campo
    # (por ejemplo, sin originPlanet).
    return plano.reindex(columns=list(MAPEO_COLUMNAS)).rename(columns=MAPEO_COLUMNAS)

LIMITE_BIGINT = 9_223_372_036_854_775_807


def _parsear_ki(valor):
    """'60.000.000' -> 60000000. Textos como '90 Septillion' o 'unknown' -> None (NULL).

    Si el número no cabe en un BIGINT también devuelve None.
    """
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+|\d+", texto):
        numero = int(texto.replace(".", ""))
        return numero if numero <= LIMITE_BIGINT else None
    return None


def _limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """T (2): nulos, tipos de datos y duplicados."""
    pk = next(iter(Entidad.__table__.primary_key.columns)).name

    # Texto: nulos y vacíos -> "N/A"
    for col in COLUMNAS_TEXTO:
        df[col] = df[col].fillna("N/A").astype(str).str.strip().replace("", "N/A")

    # ki: texto -> entero; lo que no sea número queda NULL
    df["ki_base"] = df["ki_base"].apply(_parsear_ki).astype("Int64")

    # Numéricos y fechas: se dejan como NULL (no se rellenan con 0 ni con "N/A")
    for col in COLUMNAS_NUMERICAS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in COLUMNAS_FECHA:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True).dt.date

    df[pk] = df[pk].astype(ID_TIPO)
    df = df.drop_duplicates(subset=pk)

    # NaN / NaT / <NA> -> None para que MySQL guarde NULL (y los tipos queden como Python nativos).
    # planeta_destruido queda True / False / None (None si el personaje no tiene planeta).
    return df.astype(object).where(df.notna(), None)

def _cargar_upsert(db: Session, df: pd.DataFrame) -> int:
    """L: inserta por lotes con ON DUPLICATE KEY UPDATE (no duplica por PK)."""
    registros = df.to_dict(orient="records")
    columnas_actualizables = [c.name for c in Entidad.__table__.columns if not c.primary_key]

    for i in range(0, len(registros), 500):
        lote = registros[i : i + 500]
        stmt = mysql_insert(Entidad).values(lote)
        stmt = stmt.on_duplicate_key_update(
            {col: stmt.inserted[col] for col in columnas_actualizables}
        )
        db.execute(stmt)
    db.commit()
    return len(registros)