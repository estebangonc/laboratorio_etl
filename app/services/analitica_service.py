import pandas as pd
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, select
from sqlalchemy.orm import Session

from ..models.entidad_sql import Entidad


def columnas_validas() -> list[str]:
    """Nombres de las columnas de la tabla, leídos del modelo (nada hardcodeado)."""
    return [c.name for c in Entidad.__table__.columns]


def _leer_serie(db: Session, columna) -> pd.Series:
    """Trae TODOS los valores de una columna (incluidos los NULL) como Serie de Pandas."""
    valores = db.execute(select(columna)).scalars().all()
    return pd.Series(valores, dtype="object")