"""Pydantic schemas for entities endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class EntitySummary(BaseModel):
    """Resumen de entidad para listados."""

    nit_entidad: str
    nombre_entidad: str
    total_contratos: int
    valor_total: float
    sector: Optional[str] = None


class EntityDetail(EntitySummary):
    """Detalle de entidad incluyendo contratos recientes."""

    departamento: Optional[str] = None
    ciudad: Optional[str] = None
