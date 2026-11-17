import pandas as pd
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, select
from sqlalchemy.orm import Session

from ..database import get_mongo_collection
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


def _num(valor: float):
    """Entero si no tiene decimales; si no, redondeado a 2 decimales."""
    valor = float(valor)
    return int(valor) if valor.is_integer() else round(valor, 2)


def analizar_columna(db: Session, nombre: str) -> dict | None:
    """Análisis estadístico de una columna según su tipo detectado.
    Devuelve None si la tabla está vacía.
    """
    columna = Entidad.__table__.columns[nombre]
    serie = _leer_serie(db, columna)
    if serie.empty:
        return None

    nulos = int(serie.isna().sum())
    no_nulos = serie.dropna()
    tipo = _detectar_tipo(columna, serie)
    base = {"columna": nombre, "tipo": tipo}

    if no_nulos.empty:
        return {**base, "nulos": nulos}

    if tipo == "categorica":
        conteo = no_nulos.value_counts()
        return {
            **base,
            "valores_unicos": int(conteo.size),
            "distribucion": {str(valor): int(n) for valor, n in conteo.items()},
            "valor_mas_comun": str(conteo.idxmax()),
            "nulos": nulos,
        }

    if tipo == "numerica":
        numeros = pd.to_numeric(no_nulos, errors="coerce").dropna().astype(float)
        return {
            **base,
            "min": _num(numeros.min()),
            "max": _num(numeros.max()),
            "promedio": round(float(numeros.mean()), 2),
            "mediana": _num(numeros.median()),
            "desviacion_std": round(float(numeros.std()), 2) if len(numeros) > 1 else 0.0,
            "nulos": nulos,
        }

    if tipo == "fecha":
        fechas = pd.to_datetime(no_nulos, errors="coerce").dropna()
        minimo, maximo = fechas.min(), fechas.max()
        return {
            **base,
            "min": minimo.date().isoformat(),
            "max": maximo.date().isoformat(),
            "rango_dias": int((maximo - minimo).days),
            "nulos": nulos,
        }

    if tipo == "booleana":
        return {
            **base,
            "true": int((no_nulos == 1).sum()),
            "false": int((no_nulos == 0).sum()),
            "nulos": nulos,
        }

    # texto libre
    return {**base, "valores_unicos": int(no_nulos.nunique()), "nulos": nulos}


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