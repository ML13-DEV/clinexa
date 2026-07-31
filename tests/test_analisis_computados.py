"""Campos computados del catálogo de análisis (ver
app/especialidades/analisis_config.py: CampoAnalisis.computado y
recalcular_computados). indice_cintura_cadera (Nutrición) es el primero:
se recalcula en el backend a partir de circunferencia_cintura/cadera, y
cualquier valor que mande el cliente para esa key se ignora."""

from tests.conftest import auth_headers


def _crear_paciente(client, token, dni="1"):
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


def test_icc_se_calcula_al_crear_con_cintura_y_cadera(client, crear_medico):
    _, token = crear_medico("dr_icc1", "nutricion")
    paciente_id = _crear_paciente(client, token)

    res = client.post(
        "/analisis",
        json={
            "paciente_id": paciente_id,
            "fecha": "2026-07-31",
            "circunferencia_cintura": "90",
            "circunferencia_cadera": "100",
        },
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    assert res.json()["indice_cintura_cadera"] == 0.9


def test_icc_no_se_calcula_si_falta_un_dato(client, crear_medico):
    _, token = crear_medico("dr_icc2", "nutricion")
    paciente_id = _crear_paciente(client, token)

    res = client.post(
        "/analisis",
        json={
            "paciente_id": paciente_id,
            "fecha": "2026-07-31",
            "circunferencia_cintura": "90",
        },
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    assert res.json().get("indice_cintura_cadera") is None


def test_icc_ignora_valor_manual_del_cliente(client, crear_medico):
    _, token = crear_medico("dr_icc3", "nutricion")
    paciente_id = _crear_paciente(client, token)

    res = client.post(
        "/analisis",
        json={
            "paciente_id": paciente_id,
            "fecha": "2026-07-31",
            "circunferencia_cintura": "90",
            "circunferencia_cadera": "100",
            "indice_cintura_cadera": "999",
        },
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    assert res.json()["indice_cintura_cadera"] == 0.9


def test_icc_se_recalcula_en_update_parcial(client, crear_medico):
    _, token = crear_medico("dr_icc4", "nutricion")
    paciente_id = _crear_paciente(client, token)

    res = client.post(
        "/analisis",
        json={
            "paciente_id": paciente_id,
            "fecha": "2026-07-31",
            "circunferencia_cintura": "80",
            "circunferencia_cadera": "100",
        },
        headers=auth_headers(token),
    )
    assert res.json()["indice_cintura_cadera"] == 0.8
    analisis_id = res.json()["id"]

    # Update parcial: solo toca cadera, cintura sigue siendo la guardada (80)
    res = client.put(
        f"/analisis/{analisis_id}",
        json={"circunferencia_cadera": "160"},
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    assert res.json()["indice_cintura_cadera"] == 0.5


def test_icc_se_borra_si_se_quita_uno_de_los_campos(client, crear_medico):
    _, token = crear_medico("dr_icc5", "nutricion")
    paciente_id = _crear_paciente(client, token)

    res = client.post(
        "/analisis",
        json={
            "paciente_id": paciente_id,
            "fecha": "2026-07-31",
            "circunferencia_cintura": "80",
            "circunferencia_cadera": "100",
        },
        headers=auth_headers(token),
    )
    analisis_id = res.json()["id"]
    assert res.json()["indice_cintura_cadera"] == 0.8

    res = client.put(
        f"/analisis/{analisis_id}",
        json={"circunferencia_cadera": None},
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    assert res.json().get("indice_cintura_cadera") is None
    assert res.json().get("circunferencia_cadera") is None


def test_catalogo_analisis_expone_flag_computado(client, crear_medico):
    _, token = crear_medico("dr_icc6", "nutricion")

    res = client.get("/especialidades/analisis", headers=auth_headers(token))
    assert res.status_code == 200, res.text
    catalogo = {c["key"]: c for c in res.json()}

    assert catalogo["indice_cintura_cadera"]["computado"] is True
    assert catalogo["peso"]["computado"] is False


def test_nuevos_campos_cardiologia_y_neurologia_son_aceptados(client, crear_medico):
    _, token_cardio = crear_medico("dr_cardio1", "cardiologia")
    paciente_cardio = _crear_paciente(client, token_cardio, dni="c1")

    res = client.post(
        "/analisis",
        json={
            "paciente_id": paciente_cardio,
            "fecha": "2026-07-31",
            "peso": "82",
            "saturacion_oxigeno": "98",
        },
        headers=auth_headers(token_cardio),
    )
    assert res.status_code == 200, res.text

    _, token_neuro = crear_medico("dr_neuro1", "neurologia")
    paciente_neuro = _crear_paciente(client, token_neuro, dni="n1")

    res = client.post(
        "/analisis",
        json={
            "paciente_id": paciente_neuro,
            "fecha": "2026-07-31",
            "frecuencia_episodios": "3",
            "puntaje_cognitivo": "27",
        },
        headers=auth_headers(token_neuro),
    )
    assert res.status_code == 200, res.text
