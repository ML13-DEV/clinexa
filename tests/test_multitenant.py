"""Aislamiento multi-tenant: un médico nunca debe poder leer/editar/borrar
pacientes, notas ni análisis de otro médico. Es lo más crítico del
proyecto (ver app/core/permissions.py) porque todos los médicos comparten
la misma base."""

from tests.conftest import auth_headers


def _crear_paciente(client, token, dni="111"):
    body = {
        "nombre": "Juan",
        "apellido": "Perez",
        "dni": dni,
        "fecha_nacimiento": "1990-01-01",
        "datos_clinicos": {},
    }
    res = client.post("/pacientes", json=body, headers=auth_headers(token))
    assert res.status_code == 200, res.text
    return res.json()["id"]


def test_medico_no_ve_pacientes_de_otro(client, crear_medico):
    _, token_a = crear_medico("dra", "hematologia")
    _, token_b = crear_medico("drb", "hematologia")

    paciente_id = _crear_paciente(client, token_a)

    res = client.get(f"/pacientes/{paciente_id}", headers=auth_headers(token_b))
    assert res.status_code == 404

    res = client.get("/pacientes", headers=auth_headers(token_b))
    assert res.status_code == 200
    assert res.json() == []


def test_medico_no_puede_editar_ni_borrar_paciente_de_otro(client, crear_medico):
    _, token_a = crear_medico("dra2", "hematologia")
    _, token_b = crear_medico("drb2", "hematologia")

    paciente_id = _crear_paciente(client, token_a)

    res = client.put(
        f"/pacientes/{paciente_id}", json={"nombre": "Hackeado"}, headers=auth_headers(token_b)
    )
    assert res.status_code == 404

    res = client.delete(f"/pacientes/{paciente_id}", headers=auth_headers(token_b))
    assert res.status_code == 404

    # el paciente sigue intacto para su dueño real
    res = client.get(f"/pacientes/{paciente_id}", headers=auth_headers(token_a))
    assert res.status_code == 200
    assert res.json()["paciente"]["nombre"] == "Juan"


def test_medico_no_ve_notas_de_paciente_ajeno(client, crear_medico):
    _, token_a = crear_medico("dra3", "hematologia")
    _, token_b = crear_medico("drb3", "hematologia")

    paciente_id = _crear_paciente(client, token_a)

    res = client.post(
        "/notas",
        json={"paciente_id": paciente_id, "contenido": "nota confidencial"},
        headers=auth_headers(token_a),
    )
    assert res.status_code == 200, res.text
    nota_id = res.json()["id"]

    # B ni siquiera puede crear una nota sobre el paciente de A
    res = client.post(
        "/notas",
        json={"paciente_id": paciente_id, "contenido": "intento ajeno"},
        headers=auth_headers(token_b),
    )
    assert res.status_code == 404

    res = client.put(
        f"/notas/{nota_id}", json={"contenido": "editado"}, headers=auth_headers(token_b)
    )
    assert res.status_code == 404

    res = client.delete(f"/notas/{nota_id}", headers=auth_headers(token_b))
    assert res.status_code == 404


def test_medico_no_ve_analisis_de_paciente_ajeno(client, crear_medico):
    _, token_a = crear_medico("dra4", "hematologia")
    _, token_b = crear_medico("drb4", "hematologia")

    paciente_id = _crear_paciente(client, token_a)

    res = client.post(
        "/analisis",
        json={"paciente_id": paciente_id, "fecha": "2026-07-28", "gb": "5.5"},
        headers=auth_headers(token_a),
    )
    assert res.status_code == 200, res.text
    analisis_id = res.json()["id"]

    # B no puede crear analisis sobre el paciente de A
    res = client.post(
        "/analisis",
        json={"paciente_id": paciente_id, "fecha": "2026-07-28", "gb": "1"},
        headers=auth_headers(token_b),
    )
    assert res.status_code == 404

    # ni leer, editar o borrar el analisis ya creado
    res = client.get(f"/analisis/{paciente_id}", headers=auth_headers(token_b))
    assert res.status_code == 404

    res = client.put(f"/analisis/{analisis_id}", json={"gb": "9"}, headers=auth_headers(token_b))
    assert res.status_code == 404

    res = client.delete(f"/analisis/{analisis_id}", headers=auth_headers(token_b))
    assert res.status_code == 404
