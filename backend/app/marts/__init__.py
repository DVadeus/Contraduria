"""Data Marts — capa de agregación analítica para Contraduria.

Los Data Marts se construyen automáticamente después del ETL
y generan métricas precalculadas para mejorar el rendimiento de la API.

Arquitectura:
    ETL → GOLD → DATA MARTS → DuckDB VIEWS → API

Marts incluidos:
- mart_entidades: agregado por entidad + año
- mart_proveedores: agregado por proveedor + año
- mart_temporal: agregado por año + mes
- mart_modalidades: agregado por modalidad + año (con participación %)
"""

from app.marts.mart_builder import MartBuilder

__all__ = ["MartBuilder"]
