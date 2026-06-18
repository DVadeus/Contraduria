"""ContractService — reglas de negocio para contratos.

Orquesta ContractRepository y transforma resultados en schemas Pydantic.
"""

import math
from typing import Any

import duckdb

from app.core.exceptions import NotFoundError
from app.repositories import contract_repository
from app.schemas.common import PaginatedResponse
from app.schemas.contracts import ContractDetail, ContractSummary


def list_contracts(
    conn: duckdb.DuckDBPyConnection,
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 50,
) -> PaginatedResponse[ContractSummary]:
    """Lista contratos con filtros y paginación.

    Args:
        conn: Conexión DuckDB.
        filters: Diccionario de filtros (anio, entidad, proveedor, etc.)
        page: Página solicitada (1-based).
        page_size: Registros por página.

    Returns:
        PaginatedResponse con ContractSummary.
    """
    offset = (page - 1) * page_size
    rows = contract_repository.find_all(conn, filters, offset=offset, limit=page_size)
    total = contract_repository.count_all(conn, filters)
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    summaries = [ContractSummary(**row) for row in rows]

    return PaginatedResponse(
        data=summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_by_id(conn: duckdb.DuckDBPyConnection, id_contrato: str) -> ContractDetail:
    """Obtiene el detalle completo de un contrato por su ID.

    Args:
        conn: Conexión DuckDB.
        id_contrato: Identificador del contrato.

    Returns:
        ContractDetail.

    Raises:
        NotFoundError: Si el contrato no existe.
    """
    row = contract_repository.find_by_id(conn, id_contrato)
    if row is None:
        raise NotFoundError(f"Contrato con ID '{id_contrato}' no encontrado")
    return ContractDetail(**row)
