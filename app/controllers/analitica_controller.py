from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import analitica_service
from ..views import schemas

router = APIRouter(prefix="/api/v1/analitica", tags=["Analítica"])



@router.get("/columna/{nombre}", response_model=schemas.AnalisisColumnaResponse)
def analisis_columna_endpoint(nombre: str, db: Session = Depends(get_db)):
    return analitica_service.analizar_columna(db, nombre)