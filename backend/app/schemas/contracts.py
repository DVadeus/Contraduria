"""Pydantic schemas for contracts endpoints."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ContractSummary(BaseModel):
    """Resumen de contrato para listados paginados."""

    id_contrato: str
    nombre_entidad: Optional[str] = None
    proveedor_adjudicado: Optional[str] = None
    valor_contrato: Optional[float] = None
    fecha_firma: Optional[date] = None
    estado_contrato: Optional[str] = None
    modalidad_contratacion: Optional[str] = None


class ContractDetail(ContractSummary):
    """Detalle completo de un contrato."""

    nit_entidad: Optional[str] = None
    departamento: Optional[str] = None
    ciudad: Optional[str] = None
    objeto_contrato: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    valor_pagado: Optional[float] = None
    valor_facturado: Optional[float] = None
    documento_proveedor: Optional[str] = None
    url_proceso: Optional[str] = None
    tipo_contrato: Optional[str] = None
    duracion_contrato: Optional[str] = None
    dias_adicionados: Optional[int] = None
    localizacion: Optional[str] = None
    sector: Optional[str] = None
    rama: Optional[str] = None
    origen_recursos: Optional[str] = None
    destino_gasto: Optional[str] = None
    es_postconflicto: Optional[str] = None


class ContractFilters(BaseModel):
    """Filtros para búsqueda de contratos."""

    anio: Optional[int] = Field(default=None, ge=2000, le=2100)
    entidad: Optional[str] = Field(default=None, description="Nombre o NIT de entidad")
    proveedor: Optional[str] = Field(
        default=None, description="Nombre o documento de proveedor"
    )
    modalidad: Optional[str] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    valor_min: Optional[float] = Field(default=None, ge=0)
    valor_max: Optional[float] = Field(default=None, ge=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
