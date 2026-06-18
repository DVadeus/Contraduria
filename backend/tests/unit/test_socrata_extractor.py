"""Tests unitarios para socrata_extractor.

Verifica:
- fetch_page: éxito, timeout, HTTP error, respuesta no-lista, reintentos.
- extract_dataset: paginación, detección de fin, guardado de archivos.
"""

import json
from unittest.mock import Mock, patch

import httpx
import pytest
from etl.extract.socrata_extractor import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    _build_headers,
    extract_dataset,
    fetch_page,
)

# ---------------------------------------------------------------------------
# fetch_page tests
# ---------------------------------------------------------------------------


class TestFetchPage:
    """Tests para la función fetch_page."""

    def test_successful_fetch(self):
        """fetch_page debe devolver los datos en una lista cuando la respuesta es exitosa."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"id_contrato": "001", "nombre_entidad": "Secretaría de Salud"}
        ]

        mock_client = Mock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        params = {"$limit": 10, "$offset": 0}
        result = fetch_page(mock_client, DEFAULT_BASE_URL, params)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id_contrato"] == "001"
        mock_client.get.assert_called_once_with(
            DEFAULT_BASE_URL, params=params, timeout=DEFAULT_TIMEOUT
        )

    def test_timeout_with_retry(self):
        """fetch_page debe reintentar ante timeout y fallar tras agotar intentos."""
        mock_client = Mock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.TimeoutException("Timeout simulado")

        params = {"$limit": 10, "$offset": 0}
        with pytest.raises(httpx.HTTPError, match="Fallo en los 3 intentos"):
            fetch_page(
                mock_client,
                DEFAULT_BASE_URL,
                params,
                max_retries=3,
                backoff=0.01,  # Backoff mínimo para test rápido
            )

        assert mock_client.get.call_count == 3

    def test_http_error_with_retry(self):
        """fetch_page debe reintentar ante HTTPStatusError."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error HTTP", request=Mock(), response=Mock(status_code=500)
        )

        mock_client = Mock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        params = {"$limit": 10, "$offset": 0}
        with pytest.raises(httpx.HTTPError):
            fetch_page(
                mock_client,
                DEFAULT_BASE_URL,
                params,
                max_retries=2,
                backoff=0.01,
            )

        assert mock_client.get.call_count == 2

    def test_non_list_response(self):
        """fetch_page debe devolver lista vacía si Socrata no devuelve una lista."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"error": "rate limit exceeded"}

        mock_client = Mock(spec=httpx.Client)
        mock_client.get.return_value = mock_response

        params = {"$limit": 10, "$offset": 0}
        result = fetch_page(mock_client, DEFAULT_BASE_URL, params)

        assert result == []

    def test_retry_succeeds_on_second_attempt(self):
        """fetch_page debe tener éxito en el segundo intento si el primero falla."""
        fail_response = Mock(spec=httpx.Response)
        fail_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock(status_code=503)
        )

        success_response = Mock(spec=httpx.Response)
        success_response.raise_for_status.return_value = None
        success_response.json.return_value = [{"id": "test"}]

        mock_client = Mock(spec=httpx.Client)
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Error", request=Mock(), response=Mock(status_code=503)
        )
        # Simular: primer intento falla, segundo tiene éxito
        mock_client.get.side_effect = [
            httpx.HTTPStatusError(
                "Error", request=Mock(), response=Mock(status_code=503)
            ),
        ]
        # Necesitamos un enfoque diferente: mock_client.get retorna respuesta
        # pero raise_for_status lanza excepción en el primer intento
        mock_client.reset_mock()
        mock_client.get = Mock()
        mock_client.get.side_effect = [
            httpx.TimeoutException("Timeout"),
            success_response,
        ]

        params = {"$limit": 10, "$offset": 0}
        result = fetch_page(
            mock_client,
            DEFAULT_BASE_URL,
            params,
            max_retries=3,
            backoff=0.01,
        )

        assert result == [{"id": "test"}]
        assert mock_client.get.call_count == 2


# ---------------------------------------------------------------------------
# extract_dataset tests
# ---------------------------------------------------------------------------


class TestExtractDataset:
    """Tests para la función extract_dataset."""

    def test_pagination_single_page(self, tmp_path):
        """extract_dataset debe manejar una sola página de datos."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"id_contrato": "001", "nombre_entidad": "Sec. Salud"}
        ]

        with patch("etl.extract.socrata_extractor.httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            # Primera llamada: datos, segunda: vacía → fin
            mock_client.get.side_effect = [
                mock_response,
                Mock(
                    spec=httpx.Response,
                    raise_for_status=Mock(return_value=None),
                    json=Mock(return_value=[]),
                ),
                Mock(
                    spec=httpx.Response,
                    raise_for_status=Mock(return_value=None),
                    json=Mock(return_value=[]),
                ),
                Mock(
                    spec=httpx.Response,
                    raise_for_status=Mock(return_value=None),
                    json=Mock(return_value=[]),
                ),
            ]
            mock_client_class.return_value = mock_client

            result, run_dir = extract_dataset(limit=10, raw_dir=tmp_path)

            assert result == 1
            assert run_dir.exists()
            # Debe haber creado exactamente 1 archivo JSON dentro del directorio de ejecución
            json_files = list(run_dir.glob("socrata_page_*.json"))
            assert len(json_files) == 1

    def test_pagination_multiple_pages(self, tmp_path):
        """extract_dataset debe paginar correctamente con múltiples páginas."""
        page1_response = Mock(spec=httpx.Response)
        page1_response.raise_for_status.return_value = None
        page1_response.json.return_value = [
            {"id_contrato": "001"},
            {"id_contrato": "002"},
        ]

        page2_response = Mock(spec=httpx.Response)
        page2_response.raise_for_status.return_value = None
        page2_response.json.return_value = [{"id_contrato": "003"}]

        empty_response = Mock(spec=httpx.Response)
        empty_response.raise_for_status.return_value = None
        empty_response.json.return_value = []

        with patch("etl.extract.socrata_extractor.httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            mock_client.get.side_effect = [
                page1_response,
                page2_response,
                empty_response,
                empty_response,
                empty_response,
            ]
            mock_client_class.return_value = mock_client

            result, run_dir = extract_dataset(limit=2, raw_dir=tmp_path)

            assert result == 3
            json_files = sorted(run_dir.glob("socrata_page_*.json"))
            assert len(json_files) == 2
            # Verificar contenido del primer archivo
            with open(json_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
            assert len(data) == 2

    def test_headers_include_app_token(self):
        """_build_headers debe incluir X-App-Token si SOCRATA_APP_TOKEN está configurado."""
        with patch(
            "etl.extract.socrata_extractor._SOCRATA_APP_TOKEN", "test-token-123"
        ):
            headers = _build_headers()
            assert "X-App-Token" in headers
            assert headers["X-App-Token"] == "test-token-123"

    def test_headers_without_app_token(self):
        """_build_headers no debe incluir X-App-Token si no hay variable de entorno."""
        with patch("etl.extract.socrata_extractor._SOCRATA_APP_TOKEN", None):
            headers = _build_headers()
            assert "X-App-Token" not in headers

    def test_respects_non_default_limit(self, tmp_path):
        """extract_dataset debe respetar un límite de página personalizado."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": "001"}]

        empty_response = Mock(spec=httpx.Response)
        empty_response.raise_for_status.return_value = None
        empty_response.json.return_value = []

        with patch("etl.extract.socrata_extractor.httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.__enter__ = Mock(return_value=mock_client)
            mock_client.__exit__ = Mock(return_value=False)
            mock_client.get.side_effect = [
                mock_response,
                empty_response,
                empty_response,
                empty_response,
            ]
            mock_client_class.return_value = mock_client

            custom_limit = 100
            extract_dataset(limit=custom_limit, raw_dir=tmp_path)

            # Verificar que el primer get usó el límite custom
            first_call = mock_client.get.call_args_list[0]
            assert first_call[1]["params"]["$limit"] == custom_limit
