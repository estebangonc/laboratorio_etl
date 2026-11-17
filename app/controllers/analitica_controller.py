from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import ID_TIPO
from ..database import get_db
from ..services import analitica_service
from ..views import schemas

router = APIRouter(prefix="/api/v1/analitica", tags=["Analítica"])


@router.get(
    "/perfil/{id}",
    response_model=schemas.PerfilDualResponse,
    response_model_exclude_unset=True,
)
def perfil_dual_endpoint(id: ID_TIPO, db: Session = Depends(get_db)):
    """Endpoint E: devuelve el mismo registro desde MongoDB (_id) y MySQL (PK); si solo existe en una base, avisa con warning; si no existe en ninguna, responde 404."""
    resultado = analitica_service.obtener_perfil(db, id)
    if resultado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El registro {id} no existe ni en MongoDB ni en MySQL.",
        )
    return resultado