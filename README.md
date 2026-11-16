# Laboratorio Final 2 — Pipeline ETL con FastAPI
Pipeline ETL: API pública -> MongoDB (staging, data cruda) -> MySQL (data warehouse, tabla plana),
con endpoints de analítica. Bases de Datos (UdeA).

## Cómo correrlo
**Requisitos:** Python 3.10 o superior, y MySQL y MongoDB **encendidos** (MySQL en `localhost:3306` y MongoDB en `localhost:27017`).

1. Crear y activar el entorno virtual:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate          # Windows
   source venv/bin/activate         # Mac / Linux
   ```

2. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Copiar `.env.example` como `.env` y completar las credenciales de MySQL y Mongo.
4. Crear la base `laboratorio_etl` en MySQL (las tablas las crea la app automáticamente):

   ```sql
   CREATE DATABASE laboratorio_etl CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

5. Iniciar la aplicación y abrir `http://localhost:8000/docs`:

   ```bash
   uvicorn app.main:app --reload
   ```

*Nota: al iniciar, la aplicación crea la tabla en MySQL (si no existe) gracias al modelo SQLAlchemy, y expone la documentación interactiva (Swagger UI) donde se pueden probar los 5 endpoints.*

## Fuente de datos
Dragon Ball API (<https://web.dragonball-api.com/>), entidad `characters` (personajes), con el detalle de planeta de origen y transformaciones de cada uno.

## División de responsabilidades
### Esteban
- Base del proyecto: estructura MVC, configuración y conexiones a Mongo/MySQL.
- `POST /api/v1/etl/extraer` - Descarga de la API y carga idempotente en MongoDB (`_id` = ID original).
- `DELETE /api/v1/etl/reset` - Limpia Mongo (delete_many) y MySQL (TRUNCATE).