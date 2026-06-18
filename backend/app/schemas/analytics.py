"""Esquemas Pydantic para endpoints analíticos — indicadores, comparativas y riesgos."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TopContractorsItem(BaseModel):
    """Item de ranking de contratistas."""

    contratista: str = Field(..., description="Nombre del contratista")
    total_contratos: int = Field(..., description="Número total de contratos")
    valor_total: Decimal = Field(..., description="Valor total adjudicado en COP")
    valor_promedio: Decimal = Field(
        ..., description="Valor promedio por contrato en COP"
    )


class TopContractorsResponse(BaseModel):
    """Respuesta del endpoint de top contratistas."""

    data: list[TopContractorsItem] = Field(..., description="Ranking de contratistas")
    total_contratistas: int = Field(
        ..., description="Número total de contratistas en el período"
    )
    periodo: Optional[str] = Field(None, description="Período analizado (año)")


class LocalityItem(BaseModel):
    """Datos agregados por localidad."""

    localidad: str = Field(..., description="Nombre de la localidad")
    total_contratos: int = Field(..., description="Número de contratos en la localidad")
    valor_total: Decimal = Field(..., description="Valor total en COP")
    contratistas_unicos: int = Field(..., description="Número de contratistas únicos")
    entidades_unicas: int = Field(..., description="Número de entidades contratantes")


class LocalityResponse(BaseModel):
    """Respuesta del endpoint de contratación por localidad."""

    data: list[LocalityItem] = Field(..., description="Datos por localidad")
    total_localidades: int = Field(..., description="Número de localidades analizadas")


class RiskContractItem(BaseModel):
    """Contrato marcado con indicador de riesgo."""

    proceso_id: str = Field(..., description="Identificador del proceso")
    contratista: str = Field(..., description="Nombre del contratista")
    entidad: str = Field(..., description="Entidad contratante")
    valor_contrato: Decimal = Field(..., description="Valor del contrato en COP")
    nivel_riesgo: str = Field(..., description="Nivel de riesgo: bajo, medio o alto")
    indicadores: list[str] = Field(
        default_factory=list,
        description="Indicadores de riesgo activados para este contrato",
    )


class RiskResponse(BaseModel):
    """Respuesta del endpoint de análisis de riesgo."""

    data: list[RiskContractItem] = Field(
        ..., description="Contratos con indicadores de riesgo"
    )
    total_analizados: int = Field(..., description="Total de contratos analizados")


class KPIResponse(BaseModel):
    """KPIs principales del dashboard."""

    total_contratos: int = Field(..., description="Número total de contratos")
    valor_total: Decimal = Field(..., description="Valor total en COP")
    valor_promedio: Decimal = Field(
        ..., description="Valor promedio por contrato en COP"
    )
    contratistas_unicos: int = Field(..., description="Número de contratistas únicos")
    entidades_unicas: int = Field(
        ..., description="Número de entidades contratantes únicas"
    )
    localidades_cubiertas: int = Field(
        ..., description="Número de localidades con contratos"
    )
    ano: Optional[int] = Field(None, description="Año de análisis (si se filtró)")
