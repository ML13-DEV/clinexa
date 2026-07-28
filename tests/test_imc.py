"""calcular_imc (app/routes/pacientes.py) debe recalcularse cada vez que
cambia peso o talla, tanto al crear como al editar parcialmente."""

from tests.conftest import auth_headers


def _crear_paciente(client, token, peso=None, talla=None):
    body = {
        "nombre": "Juan",
        "apellido": "Perez",
        "dni": "111",
        "fecha_nacimiento": "1990-01-01",
        "datos_clinicos": {},
        "peso": peso,
        "talla": talla,
    }
    res = client.post("/pacientes", json=body, headers=auth_headers(token))
    assert res.status_code == 200, res.text
    return res.json()


def test_imc_se_calcula_al_crear_con_peso_y_talla(client, crear_medico):
    _, token = crear_medico("drimc1", "hematologia")

    paciente = _crear_paciente(client, token, peso=70, talla=170)
    # 70 / (1.70^2) = 24.22
    assert paciente["imc"] == 24.22


def test_imc_nulo_si_falta_peso_o_talla(client, crear_medico):
    _, token = crear_medico("drimc2", "hematologia")

    paciente = _crear_paciente(client, token, peso=70, talla=None)
    assert paciente["imc"] is None


def test_imc_se_recalcula_al_actualizar_solo_peso(client, crear_medico):
    _, token = crear_medico("drimc3", "hematologia")

    paciente = _crear_paciente(client, token, peso=70, talla=170)
    paciente_id = paciente["id"]

    res = client.put(
        f"/pacientes/{paciente_id}", json={"peso": 80}, headers=auth_headers(token)
    )
    assert res.status_code == 200, res.text
    # 80 / (1.70^2) = 27.68
    assert res.json()["imc"] == 27.68


def test_imc_se_recalcula_al_actualizar_solo_talla(client, crear_medico):
    _, token = crear_medico("drimc4", "hematologia")

    paciente = _crear_paciente(client, token, peso=70, talla=170)
    paciente_id = paciente["id"]

    res = client.put(
        f"/pacientes/{paciente_id}", json={"talla": 180}, headers=auth_headers(token)
    )
    assert res.status_code == 200, res.text
    # 70 / (1.80^2) = 21.6
    assert res.json()["imc"] == 21.6


def test_imc_se_recalcula_al_actualizar_ambos(client, crear_medico):
    _, token = crear_medico("drimc5", "hematologia")

    paciente = _crear_paciente(client, token, peso=70, talla=170)
    paciente_id = paciente["id"]

    res = client.put(
        f"/pacientes/{paciente_id}",
        json={"peso": 60, "talla": 150},
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    # 60 / (1.50^2) = 26.67
    assert res.json()["imc"] == 26.67
