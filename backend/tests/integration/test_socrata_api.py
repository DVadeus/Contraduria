"""Test de integración con la API real de Socrata SECOP II.

Verifica conectividad y formato de respuesta del endpoint real.
Se ejecuta con un límite pequeño para no saturar la API.

Marcado como 'integration' para poder ejecutarse selectivamente.
"""

import httpx
import pytest
from etl.extract.socrata_extractor import fetch_page


@pytest.mark.integration
def test_socrata_api_connectivity():
    """Verifica que la API de Socrata responde correctamente con datos."""
    url = "https://www.datos.gov.co/resource/jbjy-vk9h.json"
    params = {"$limit": 5, "$offset": 0}
    headers = {
        "Accept": "application/json",
        "User-Agent": "Contraduria/0.1.0 (test suite; contacto@contraduria.org)",
    }
    # Agregar App Token si está disponible
    import os

    app_token = os.getenv("SOCRATA_APP_TOKEN")
    if app_token:
        headers["X-App-Token"] = app_token

    with httpx.Client(headers=headers, http2=True, timeout=30.0) as client:
        result = fetch_page(client, url, params, timeout=30.0, max_retries=2)

    assert isinstance(result, list), "La API debe devolver una lista"
    assert len(result) <= 5, f"Se pidieron 5 registros, se recibieron {len(result)}"
    assert len(result) > 0, (
        "La API devolvió 0 registros — posible error de conectividad"
    )

    # Verificar estructura básica del primer registro
    first = result[0]
    assert isinstance(first, dict), "Cada registro debe ser un diccionario"
    assert "id_contrato" in first or "nombre_entidad" in first, (
        "El registro debe contener campos del dataset SECOP II"
    )


@pytest.mark.integration
def test_socrata_api_pagination_consistency():
    """Verifica que dos páginas consecutivas no se solapan (offsets correctos)."""
    url = "https://www.datos.gov.co/resource/jbjy-vk9h.json"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Contraduria/0.1.0 (test suite; contacto@contraduria.org)",
    }
    import os

    app_token = os.getenv("SOCRATA_APP_TOKEN")
    if app_token:
        headers["X-App-Token"] = app_token

    limit = 3

    with httpx.Client(headers=headers, http2=True, timeout=30.0) as client:
        page1 = fetch_page(client, url, {"$limit": limit, "$offset": 0})
        page2 = fetch_page(client, url, {"$limit": limit, "$offset": limit})

    if len(page1) == 0 or len(page2) == 0:
        pytest.skip("API no devolvió suficientes datos para verificar paginación")

    # Los IDs de la primera y segunda página no deben solaparse
    ids_page1 = {r.get("id_contrato") for r in page1 if r.get("id_contrato")}
    ids_page2 = {r.get("id_contrato") for r in page2 if r.get("id_contrato")}

    intersection = ids_page1 & ids_page2
    assert len(intersection) == 0, (
        f"Las páginas se solapan: {intersection}. La paginación puede no ser consistente."
    )
