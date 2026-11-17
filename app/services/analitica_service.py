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

def _detectar_tipo(columna, serie: pd.Series) -> str:
    """Tipo lógico de la columna, deducido del tipo SQLAlchemy y de los datos."""
    tipo_sql = columna.type
    if isinstance(tipo_sql, Boolean):
        return "booleana"
    if isinstance(tipo_sql, (Date, DateTime)):
        return "fecha"
    no_nulos = serie.dropna()
    if isinstance(tipo_sql, (Integer, Float, Numeric)):
        # MySQL guarda BOOLEAN como TINYINT(1): una numérica que solo tiene 0 y 1 es booleana
        if not columna.primary_key and len(no_nulos) > 0 and set(no_nulos.unique()) <= {0, 1}:
            return "booleana"
        return "numerica"
    # Texto: todos distintos -> texto libre; con valores repetidos -> categórica
    if len(no_nulos) > 0 and no_nulos.nunique() == len(no_nulos):
        return "texto"
    return "categorica"