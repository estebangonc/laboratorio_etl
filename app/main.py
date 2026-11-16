from fastapi import FastAPI
from .controllers import analitica_controller, etl_controller

app = FastAPI(
    title="Laboratorio Final 2 - Pipeline ETL",
    description="API pública -> MongoDB (staging) -> MySQL (data warehouse) + analítica",
    version="1.0.0",
)

app.include_router(etl_controller.router)
app.include_router(analitica_controller.router)

@app.get("/", tags=["Estado"])
def raiz():
    return {"mensaje": "Pipeline ETL activo", "docs": "/docs"}