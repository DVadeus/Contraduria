"""Router de contratos — endpoints REST para consulta de contratos.

Responsable ÚNICAMENTE de:
- Recibir requests HTTP.
- Validar parámetros de entrada.
- Invocar servicios.
- Devolver respuestas HTTP.

No contiene lógica de negocio ni acceso a datos.
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.db.database import create_connection
from app.schemas.contracts import (
    ContractResponse,
    ErrorResponse,
    PaginatedResponse,
)
from app.services.contract_service import get_contract, list_contracts

router = APIRouter(prefix="/contracts", tags=["Contracts"])

# Directorio de datos — configurable vía variable de entorno
_DATA_DIR = os.getenv(
    "CONTRADURIA_DATA_DIR",
    str(Path(__file__).resolve().parent.parent.parent.parent / "data"),
)


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="Listar contratos",
    description="Obtiene una lista paginada de contratos ordenados por fecha de firma descendente.",
    responses={
        200: {"description": "Lista paginada de contratos"},
        503: {"model": ErrorResponse, "description": "Datos no disponibles"},
    },
)
def get_contracts(
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(50, ge=1, le=200, description="Límite de registros por página"),
):
    """Lista contratos con paginación."""
    try:
        conn = create_connection()
        result = list_contracts(conn, _DATA_DIR, offset=offset, limit=limit)
        conn.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get(
    "/{proceso_id}",
    response_model=ContractResponse,
    summary="Obtener contrato por ID",
    description="Busca un contrato por su identificador único de proceso SECOP II.",
    responses={
        200: {"description": "Contrato encontrado"},
        404: {"model": ErrorResponse, "description": "Contrato no encontrado"},
        503: {"model": ErrorResponse, "description": "Datos no disponibles"},
    },
)
def get_contract_by_id(
    proceso_id: str,
):
    """Obtiene un contrato por su ID de proceso."""
    try:
        conn = create_connection()
        contract = get_contract(conn, _DATA_DIR, proceso_id)
        conn.close()

        if contract is None:
            raise HTTPException(
                status_code=404,
                detail=f"Contrato con ID '{proceso_id}' no encontrado",
            )

        return contract
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
