from fastapi import APIRouter
from fastapi import APIRouter, status
from ..config import API_NOMBRE
from ..services import etl_service
from ..views import schemas

router = APIRouter(prefix="/api/v1/etl", tags=["ETL"])


@router.post(
    "/extraer",
    response_model=schemas.ExtraerResponse,
    status_code=status.HTTP_201_CREATED,
)
def extraer_endpoint(payload: schemas.ExtraerRequest):
    resultado = etl_service.extraer_registros(payload.cantidad)
    return {
        "mensaje": "Datos extraídos exitosamente",
        **resultado,
        "fuente": API_NOMBRE,
        "status": 201,
    }