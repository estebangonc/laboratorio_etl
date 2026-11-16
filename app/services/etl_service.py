from datetime import datetime
import requests
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