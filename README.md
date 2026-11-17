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

3. Copiar `.env.example` como `.env` y completar las credenciales de MySQL y Mongo (variables: `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DB`, `MONGO_URI`, `MONGO_DB`, `MONGO_COLLECTION`). El `.env` no se sube al repositorio.

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

## Endpoints

| Método y ruta | Descripción |
|---|---|
| `POST /api/v1/etl/extraer` | Descarga de la API y guarda la data cruda en MongoDB (idempotente) |
| `POST /api/v1/etl/transformar` | Lee Mongo, limpia con Pandas y carga en MySQL (idempotente) |
| `DELETE /api/v1/etl/reset` | Limpia Mongo (`delete_many`) y MySQL (`TRUNCATE`) |
| `GET /api/v1/analitica/columna/{nombre}` | Análisis estadístico de una columna con detección dinámica de tipo |
| `GET /api/v1/analitica/perfil/{id}` | Perfil dual: el mismo registro en Mongo y MySQL |

## Estructura del proyecto
Patrón MVC + Services:

```
laboratorio_etl/
├── .env.example · .gitignore · requirements.txt · README.md
└── app/
    ├── main.py · config.py · database.py
    ├── controllers/   etl_controller.py · analitica_controller.py
    ├── models/        entidad_sql.py
    ├── services/      etl_service.py · analitica_service.py
    └── views/         schemas.py
```

## División de responsabilidades
### Esteban
- Base del proyecto: estructura MVC, configuración y conexiones a Mongo/MySQL.
- `POST /api/v1/etl/extraer` - Descarga de la API y carga idempotente en MongoDB (`_id` = ID original).
- `DELETE /api/v1/etl/reset` - Limpia Mongo (delete_many) y MySQL (TRUNCATE).

### Dahiana
- Modelo SQL `Entidad` (tabla plana `personajes_master`, PK explícita igual al `_id` de Mongo, sin autoincremento).
- `POST /api/v1/etl/transformar`: Lee de MongoDB, aplana y limpia con Pandas (ki a número, N/A en texto, NULL en numéricos y fechas) y carga en MySQL con upsert (idempotente).

### Alejandro
- `GET /api/v1/analitica/columna/{nombre}` - Análisis estadístico de una columna con detección dinámica de tipo (categórica, numérica, fecha, booleana y texto).
- `GET /api/v1/analitica/perfil/{id}` - Perfil dual: el mismo registro en MongoDB y MySQL, con aviso de inconsistencias y 404 si no existe.