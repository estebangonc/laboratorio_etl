from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import analitica_service
from ..views import schemas

router = APIRouter(prefix="/api/v1/analitica", tags=["Analítica"])


@router.get("/columna/{nombre}", response_model=schemas.AnalisisColumnaResponse)
def analisis_columna_endpoint(nombre: str, db: Session = Depends(get_db)):
    validas = analitica_service.columnas_validas()
    if nombre not in validas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "mensaje": f"La columna '{nombre}' no existe en la tabla.",
                "columnas_validas": validas,
            },
        )
    resultado = analitica_service.analizar_columna(db, nombre)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La tabla está vacía: ejecuta /extraer y /transformar primero.",
        )
    return resultado