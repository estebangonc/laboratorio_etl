from typing import Any
from pydantic import BaseModel

class ExtraerRequest(BaseModel):
    """Cuerpo del POST /extraer: cuántos registros descargar."""
    cantidad: int

class ExtraerResponse(BaseModel):
    mensaje: str
    nuevos: int
    ya_existentes: int
    fuente: str
    status: int

class ResetResponse(BaseModel):
    mensaje: str
    mongo_docs_eliminados: int
    mysql_rows_eliminadas: int
    status: int
    