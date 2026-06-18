import httpx
from etl.extract.socrata_extractor import fetch_page


def test_fetch_first_page():
    with httpx.Client() as client:
        data = fetch_page(
            client=client,
            url="https://www.datos.gov.co/resource/jbjy-vk9h.json",
            params={
                "$limit": 10,
                "$offset": 0,
            },
        )

    assert isinstance(data, list)
    assert len(data) > 0
    assert isinstance(data[0], dict)

    row = data[0]

    expected_columns = {
        "nombre_entidad",
        "nit_entidad",
        "proceso_de_compra",
        "id_contrato",
        "valor_del_contrato",
    }

    assert expected_columns.issubset(set(row.keys()))
