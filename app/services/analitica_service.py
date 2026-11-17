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

    return {"id": id_registro, "vista_mongo": documento, "vista_sql": vista_sql}