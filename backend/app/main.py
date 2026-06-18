"""Aplicación principal FastAPI — Contraduria (Portal SECOP Bogotá).

Expone la API REST siguiendo la arquitectura:
    Router → Service → Repository → DuckDB → Parquet

Features:
- Health check con métricas de DuckDB.
- Contratos con filtros y paginación.
- Entidades y Proveedores con agregados.
- Estadísticas globales (KPIs).
- Manejo de errores estructurado.
- CORS para frontend Next.js.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    contracts,
    entities,
    health,
    modalities,
    stats,
    suppliers,
)
from app.core.config import settings
from app.core.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan de la aplicación — startup y shutdown hooks."""
    # Startup: no se necesita pre-cargar nada; DuckDB se conecta por request.
    yield
    # Shutdown: cleanup si es necesario.


app = FastAPI(
    title="Contraduria API — Portal SECOP Bogotá",
    description=(
        "API REST para consulta, análisis y visualización de datos de contratación "
        "pública de Bogotá, obtenidos desde el dataset oficial de SECOP II "
        "publicado en datos.gov.co mediante la API Socrata (SODA)."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    contact={
        "name": "Contraduria",
        "url": "https://github.com/DVadeus/Contraduria",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS — permitir frontend Next.js en desarrollo y producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar exception handlers personalizados
register_error_handlers(app)

# Registrar routers
app.include_router(health.router)
app.include_router(contracts.router)
app.include_router(entities.router)
app.include_router(suppliers.router)
app.include_router(modalities.router)
app.include_router(stats.router)
