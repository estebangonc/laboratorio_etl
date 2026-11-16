# Laboratorio Final 2 — Pipeline ETL con FastAPI
Pipeline ETL: API pública -> MongoDB (staging, data cruda) -> MySQL (data warehouse, tabla plana),
con endpoints de analítica. Bases de Datos (UdeA).

## Cómo correrlo
1. `python -m venv venv` y activar el entorno.
2. `pip install -r requirements.txt`
3. Copiar `.env.example` a `.env` y completar las credenciales de MySQL y Mongo.
4. Crear la base `laboratorio_etl` en MySQL (las tablas las crea la app automáticamente):
   ```sql
   CREATE DATABASE laboratorio_etl CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
5. `uvicorn app.main:app --reload` y abrir `http://localhost:8000/docs`.
*Nota: Al iniciar, la aplicación creará automáticamente la tabla en MySQL (si no existe) gracias al modelo SQLAlchemy, y expondrá la documentación interactiva (Swagger UI) donde podrán probar los 5 endpoints.*

## Fuente de datos
Dragon Ball API (<https://web.dragonball-api.com/>), entidad `characters` (personajes), con el detalle de planeta de origen y transformaciones de cada uno.

## División de responsabilidades
### Esteban
- Base del proyecto: estructura MVC, configuración y conexiones a Mongo/MySQL.
- `POST /api/v1/etl/extraer` - Descarga de la API y carga idempotente en MongoDB (`_id` = ID original).
- `DELETE /api/v1/etl/reset` - Limpia Mongo (delete_many) y MySQL (TRUNCATE).