from contextlib import asynccontextmanager

from fastapi import FastAPI

from .controllers import analitica_controller, etl_controller
from .database import Base, engine
from .models import entidad_sql  # noqa: F401 (registra la tabla en Base.metadata)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # crea la tabla si no existe
    yield


app = FastAPI(
    title="Laboratorio Final 2 - Pipeline ETL",
    description="Dragon Ball API -> MongoDB (staging) -> MySQL (data warehouse) + analítica",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(etl_controller.router)
app.include_router(analitica_controller.router)


@app.get("/", tags=["Estado"])
def raiz():
    return {"mensaje": "Pipeline ETL activo", "docs": "/docs"}