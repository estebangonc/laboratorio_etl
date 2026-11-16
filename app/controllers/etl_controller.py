from ..config import API_NOMBRE
from ..services import etl_service
from ..views import schemas
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db


router = APIRouter(prefix="/api/v1/etl", tags=["ETL"])


@router.post(
    "/extraer",
    response_model=schemas.ExtraerResponse,
    status_code=status.HTTP_201_CREATED,
)
def extraer_endpoint(payload: schemas.ExtraerRequest):
    """Endpoint A: descarga `cantidad` objetos de la API pública y los guarda crudos
    en MongoDB con upsert por _id (idempotente: reporta nuevos y ya_existentes)."""
    if payload.cantidad <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cantidad debe ser un entero mayor que 0.",
        )
    try:
        resultado = etl_service.extraer_registros(payload.cantidad)
    except requests.RequestException as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo consultar la API pública: {error}",
        )
    return {
        "mensaje": "Datos extraídos exitosamente",
        **resultado,
        "fuente": API_NOMBRE,
        "status": 201,
    }

@router.delete("/reset", response_model=schemas.ResetResponse)
def reset_endpoint(db: Session = Depends(get_db)):
    """Endpoint C: elimina todos los documentos de Mongo y vacía la tabla MySQL con
    TRUNCATE (la tabla y su PK permanecen)."""
    resultado = etl_service.reset_sistema(db)
    return {"mensaje": "Sistema reseteado correctamente", **resultado, "status": 200}