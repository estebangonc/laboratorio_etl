from datetime import datetime
import requests
from pymongo import UpdateOne
from ..config import API_URL, ID_CAMPO
from ..database import get_mongo_collection

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