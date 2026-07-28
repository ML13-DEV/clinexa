"""El formulario dinámico de paciente/análisis solo debe aceptar las keys
que el catálogo de la especialidad del médico define (ver
app/especialidades/config.py y analisis_config.py)."""

from tests.conftest import auth_headers


def _paciente_body(datos_clinicos):
    return {
        "nombre": "Juan",
        "apellido": "Perez",
        "dni": "111",
        "fecha_nacimiento": "1990-01-01",
        "datos_clinicos": datos_clinicos,
    }


def test_rechaza_campo_fuera_del_catalogo_de_la_especialidad(client, crear_medico):
    _, token = crear_medico("drval1", "nutricion")

    res = client.post(
        "/pacientes",
        json=_paciente_body({"campo_de_otra_especialidad": "x"}),
        headers=auth_headers(token),
    )
    assert res.status_code == 422
    assert "campo_de_otra_especialidad" in res.json()["detail"]


def test_rechaza_valor_no_numerico_en_campo_numero(client, crear_medico):
    _, token = crear_medico("drval2", "nutricion")

    res = client.post(
        "/pacientes",
        json=_paciente_body({"objetivo_peso": "no soy un numero"}),
        headers=auth_headers(token),
    )
    assert res.status_code == 422


def test_rechaza_opcion_invalida_en_select(client, crear_medico):
    _, token = crear_medico("drval3", "nutricion")

    res = client.post(
        "/pacientes",
        json=_paciente_body({"actividad_fisica": "volando"}),
        headers=auth_headers(token),
    )
    assert res.status_code == 422


def test_acepta_datos_clinicos_validos_de_la_especialidad(client, crear_medico):
    _, token = crear_medico("drval4", "nutricion")

    res = client.post(
        "/pacientes",
        json=_paciente_body({"objetivo_peso": "70", "actividad_fisica": "moderada"}),
        headers=auth_headers(token),
    )
    assert res.status_code == 200


def test_analisis_rechaza_key_fuera_de_catalogo(client, crear_medico):
    _, token = crear_medico("drval5", "hematologia")

    res = client.post(
        "/pacientes", json=_paciente_body({}), headers=auth_headers(token)
    )
    paciente_id = res.json()["id"]

    res = client.post(
        "/analisis",
        json={"paciente_id": paciente_id, "fecha": "2026-07-28", "glucemia": "90"},
        headers=auth_headers(token),
    )
    assert res.status_code == 422
    assert "glucemia" in res.json()["detail"]


def test_analisis_rechaza_valor_no_numerico(client, crear_medico):
    _, token = crear_medico("drval6", "hematologia")

    res = client.post(
        "/pacientes", json=_paciente_body({}), headers=auth_headers(token)
    )
    paciente_id = res.json()["id"]

    res = client.post(
        "/analisis",
        json={"paciente_id": paciente_id, "fecha": "2026-07-28", "hb": "alto"},
        headers=auth_headers(token),
    )
    assert res.status_code == 422


def test_analisis_acepta_campo_de_texto_libre_sin_chequeo_numerico(client, crear_medico):
    _, token = crear_medico("drval7", "hematologia")

    res = client.post(
        "/pacientes", json=_paciente_body({}), headers=auth_headers(token)
    )
    paciente_id = res.json()["id"]

    res = client.post(
        "/analisis",
        json={
            "paciente_id": paciente_id,
            "fecha": "2026-07-28",
            "hepatograma": "sin alteraciones",
        },
        headers=auth_headers(token),
    )
    assert res.status_code == 200
