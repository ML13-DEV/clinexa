"""Fase A de suscripciones: registro publico con aprobacion del owner.
Un medico que se registra solo (POST /registro) queda en estado
'pendiente' y no puede loguearse hasta que el owner lo apruebe; el
owner tambien puede rechazar o suspender, y ambos casos bloquean el
login con un mensaje especifico (ver EstadoCuenta)."""

from tests.conftest import auth_headers


def _registrar(client, username="drnuevo", especialidad="hematologia"):
    return client.post(
        "/registro",
        json={
            "nombre": "Dr. Nuevo",
            "username": username,
            "email": f"{username}@example.com",
            "password": "test1234",
            "especialidad": especialidad,
        },
    )


def _login(client, username, password="test1234"):
    return client.post("/login", json={"username": username, "password": password})


def test_especialidades_es_publico(client):
    res = client.get("/especialidades")
    assert res.status_code == 200
    assert "hematologia" in res.json()


def test_registro_crea_usuario_pendiente_sin_token(client, db_session):
    res = _registrar(client)
    assert res.status_code == 201
    assert "access_token" not in res.json()

    from app.models.usuario import Usuario
    usuario = db_session.query(Usuario).filter_by(username="drnuevo").first()
    assert usuario.estado == "pendiente"
    assert usuario.rol == "medico"
    assert usuario.nombre == "Dr. Nuevo"


def test_registro_ignora_rol_enviado_por_el_cliente(client, db_session):
    res = client.post(
        "/registro",
        json={
            "nombre": "Intento Owner",
            "username": "intento_owner",
            "email": "intento_owner@example.com",
            "password": "test1234",
            "especialidad": "hematologia",
            "rol": "owner",
        },
    )
    assert res.status_code == 201

    from app.models.usuario import Usuario
    usuario = db_session.query(Usuario).filter_by(username="intento_owner").first()
    assert usuario.rol == "medico"


def test_registro_rechaza_especialidad_invalida(client):
    res = client.post(
        "/registro",
        json={
            "nombre": "X",
            "username": "drinvalido",
            "email": "drinvalido@example.com",
            "password": "test1234",
            "especialidad": "no_existe",
        },
    )
    assert res.status_code == 422


def test_registro_rechaza_username_duplicado(client, crear_medico):
    crear_medico("dryaexiste", "hematologia")

    res = _registrar(client, username="dryaexiste")
    assert res.status_code == 400


def test_login_bloqueado_mientras_esta_pendiente(client):
    _registrar(client, username="drpendiente")

    res = _login(client, "drpendiente")
    assert res.status_code == 403
    assert "pendiente" in res.json()["detail"].lower()


def test_owner_aprueba_y_el_medico_puede_loguearse(client, crear_owner):
    _, owner_token = crear_owner()
    _registrar(client, username="draprobar")

    res = client.get("/owner/usuarios", headers=auth_headers(owner_token))
    pendiente = next(m for m in res.json() if m["username"] == "draprobar")
    assert pendiente["estado"] == "pendiente"
    assert pendiente["nombre"] == "Dr. Nuevo"

    res = client.put(
        f"/owner/usuarios/{pendiente['id']}",
        json={"estado": "activo"},
        headers=auth_headers(owner_token),
    )
    assert res.status_code == 200
    assert res.json()["estado"] == "activo"

    res = _login(client, "draprobar")
    assert res.status_code == 200


def test_owner_rechaza_y_el_medico_sigue_bloqueado(client, crear_owner):
    _, owner_token = crear_owner()
    _registrar(client, username="drrechazar")

    res = client.get("/owner/usuarios", headers=auth_headers(owner_token))
    pendiente = next(m for m in res.json() if m["username"] == "drrechazar")

    client.put(
        f"/owner/usuarios/{pendiente['id']}",
        json={"estado": "rechazado"},
        headers=auth_headers(owner_token),
    )

    res = _login(client, "drrechazar")
    assert res.status_code == 403
    assert "rechaz" in res.json()["detail"].lower()


def test_medico_suspendido_no_puede_loguearse(client, crear_owner, crear_medico):
    _, owner_token = crear_owner()
    medico, _ = crear_medico("drsuspender", "hematologia")

    client.put(
        f"/owner/usuarios/{medico.id}",
        json={"estado": "suspendido"},
        headers=auth_headers(owner_token),
    )

    res = _login(client, "drsuspender")
    assert res.status_code == 403
    assert "desactivada" in res.json()["detail"].lower()


def test_suspender_corta_acceso_de_una_sesion_ya_abierta(client, crear_owner, crear_medico):
    """get_current_user vuelve a chequear el estado contra la base en
    cada request, no solo al loguear: si el owner suspende a un medico
    que ya tiene un token valido, el corte de acceso es inmediato."""
    _, owner_token = crear_owner()
    medico, medico_token = crear_medico("drsesion", "hematologia")

    # con la sesion recien abierta, puede pegarle a /pacientes
    res = client.get("/pacientes", headers=auth_headers(medico_token))
    assert res.status_code == 200

    client.put(
        f"/owner/usuarios/{medico.id}",
        json={"estado": "suspendido"},
        headers=auth_headers(owner_token),
    )

    # mismo token de antes, ahora bloqueado sin volver a loguearse
    res = client.get("/pacientes", headers=auth_headers(medico_token))
    assert res.status_code == 403
