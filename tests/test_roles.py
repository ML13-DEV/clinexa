"""El rol determina qué endpoints puede usar cada usuario: un owner no
gestiona pacientes (get_current_medico) y un medico no administra
usuarios (get_current_owner, endpoints /owner)."""

from tests.conftest import auth_headers


def test_medico_no_puede_pegarle_a_endpoints_de_owner(client, crear_medico):
    _, token = crear_medico("drroles1", "hematologia")

    res = client.get("/owner/usuarios", headers=auth_headers(token))
    assert res.status_code == 403

    res = client.post(
        "/owner/usuarios",
        json={"username": "nuevo", "password": "x", "rol": "medico", "especialidad": "hematologia"},
        headers=auth_headers(token),
    )
    assert res.status_code == 403


def test_owner_no_puede_gestionar_pacientes(client, crear_owner):
    _, token = crear_owner()

    res = client.get("/pacientes", headers=auth_headers(token))
    assert res.status_code == 403

    body = {
        "nombre": "Juan",
        "apellido": "Perez",
        "dni": "111",
        "fecha_nacimiento": "1990-01-01",
        "datos_clinicos": {},
    }
    res = client.post("/pacientes", json=body, headers=auth_headers(token))
    assert res.status_code == 403


def test_owner_puede_gestionar_usuarios(client, crear_owner):
    _, token = crear_owner()

    res = client.get("/owner/usuarios", headers=auth_headers(token))
    assert res.status_code == 200
