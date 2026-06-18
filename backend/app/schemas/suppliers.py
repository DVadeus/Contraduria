"""Pydantic schemas for suppliers endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SupplierSummary(BaseModel):
    """Resumen de proveedor para listados."""

    documento_proveedor: str
    proveedor_adjudicado: str
    total_contratos: int
    valor_total: float
    es_pyme: Optional[str] = None


class SupplierDetail(SupplierSummary):
    """Detalle de proveedor con contratos recientes."""
