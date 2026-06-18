"""Pydantic schemas for statistics endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class StatsResponse(BaseModel):
    """Indicadores globales de contratación."""

    total_contratos: int
    total_entidades: int
    total_proveedores: int
    valor_total_contratado: float
    valor_total_pagado: float
    anio_desde: int
    anio_hasta: int
    ultima_actualizacion: Optional[str] = None


class ModalitySummary(BaseModel):
    """Resumen de una modalidad de contratación."""

    modalidad: str
    total_contratos: int
    valor_total: float
