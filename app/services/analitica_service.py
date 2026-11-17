from sqlalchemy.orm import Session

from ..database import get_mongo_collection
from ..models.entidad_sql import Entidad


def obtener_perfil(db: Session, id_registro) -> dict | None:
    """Mismo registro visto desde Mongo (_id) y desde MySQL (PK)."""
    documento = get_mongo_collection().find_one({"_id": id_registro})
    fila = db.get(Entidad, id_registro)

    vista_sql = None
    if fila is not None:
        vista_sql = {c.name: getattr(fila, c.name) for c in Entidad.__table__.columns}

    if documento is None and fila is None:
        return None  # no existe en ninguna base -> el controller responde 404

    resultado = {"id": id_registro, "vista_mongo": documento, "vista_sql": vista_sql}
    if fila is None:
        resultado["warning"] = (
            "Registro existe en Mongo pero no en MySQL. Posiblemente no se ha ejecutado "
            "/transformar o el registro falló en la transformación."
        )
    elif documento is None:
        resultado["warning"] = (
            "Registro existe en MySQL pero no en Mongo. Posiblemente se limpió Mongo "
            "o el documento fue eliminado después de transformar."
        )
    return resultado