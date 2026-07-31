"""GET /pacientes/estadisticas: agregados de los propios pacientes del
médico logueado, filtrados por usuario_id (no confundir con
/owner/estadisticas, que es a nivel plataforma)."""

from tests.conftest import auth_headers


def _crear_paciente(client, token, dni, diagnostico=None, localidad=None, fecha_nacimiento="1990-01-01"):
    body = {
        "nombre": "Juan",
        "apellido": "Perez",
        "dni": dni,
        "fecha_nacimiento": fecha_nacimiento,
        "diagnostico_principal": diagnostico,
        "localidad": localidad,
        "datos_clinicos": {},
    }
    res = client.post("/pacientes", json=body, headers=auth_headers(token))
    assert res.status_code == 200, res.text
    return res.json()["id"]


def test_medico_no_ve_estadisticas_de_pacientes_de_otro(client, crear_medico):
    _, token_a = crear_medico("dra_stats", "hematologia")
    _, token_b = crear_medico("drb_stats", "hematologia")

    _crear_paciente(client, token_a, dni="1", diagnostico="Anemia", localidad="La Plata")
    _crear_paciente(client, token_a, dni="2", diagnostico="anemia", localidad="la plata")

    # B no tiene pacientes propios: sus estadisticas no deben ver los de A
    res = client.get("/pacientes/estadisticas", headers=auth_headers(token_b))
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_pacientes"] == 0
    assert data["top_diagnosticos"] == []
    assert data["top_localidades"] == []
    assert sum(r["cantidad"] for r in data["rango_etario"]) == 0

    res = client.get("/pacientes/estadisticas", headers=auth_headers(token_a))
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_pacientes"] == 2


def test_normaliza_diagnostico_y_localidad_case_insensitive(client, crear_medico):
    _, token = crear_medico("dr_norm", "hematologia")

    _crear_paciente(client, token, dni="10", diagnostico="Anemia", localidad="La Plata")
    _crear_paciente(client, token, dni="11", diagnostico="ANEMIA", localidad="la plata")
    _crear_paciente(client, token, dni="12", diagnostico="  anemia  ", localidad="LA PLATA")

    res = client.get("/pacientes/estadisticas", headers=auth_headers(token))
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["top_diagnosticos"] == [{"label": "Anemia", "cantidad": 3}]
    assert data["top_localidades"] == [{"label": "La Plata", "cantidad": 3}]


def test_distribucion_por_rango_etario(client, crear_medico):
    _, token = crear_medico("dr_edad", "hematologia")

    _crear_paciente(client, token, dni="20", fecha_nacimiento="2015-01-01")  # 0-17
    _crear_paciente(client, token, dni="21", fecha_nacimiento="2000-01-01")  # 18-30
    _crear_paciente(client, token, dni="22", fecha_nacimiento="1960-01-01")  # 61+

    res = client.get("/pacientes/estadisticas", headers=auth_headers(token))
    assert res.status_code == 200, res.text
    conteos = {r["rango"]: r["cantidad"] for r in res.json()["rango_etario"]}

    assert conteos["0-17"] == 1
    assert conteos["18-30"] == 1
    assert conteos["61+"] == 1
    assert conteos["31-45"] == 0
    assert conteos["46-60"] == 0


def test_owner_no_puede_pegarle_a_estadisticas_de_medico(client, crear_owner):
    _, token_owner = crear_owner()

    res = client.get("/pacientes/estadisticas", headers=auth_headers(token_owner))
    assert res.status_code == 403
