"""GET /turnos/recientes: proximos turnos, mas cercanos primero.

Cubre dos cosas:
- skip/limit reales (antes tenia un .limit(10) fijo en el backend, asi
  que nunca se podia ver mas alla del turno 10 sin importar cuanto se
  clickeara "ver mas" en el frontend).
- El filtro/orden nuevo: fecha >= ahora, ASC (antes era fecha.desc() sin
  filtro, que con turnos cargados a futuro mostraba primero el mas
  lejano en el tiempo, no el mas proximo)."""

from datetime import datetime, timedelta

from tests.conftest import auth_headers


def _fecha_futura(dias):
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%S")


def _fecha_pasada(dias):
    return (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%S")


def _crear_turno(client, token, fecha, motivo="Control"):
    res = client.post(
        "/turnos",
        json={"nombre_temp": "Paciente Walk-in", "fecha": fecha, "motivo": motivo},
        headers=auth_headers(token),
    )
    assert res.status_code == 200, res.text
    return res.json()


def test_limit_por_defecto_es_5(client, crear_medico):
    _, token = crear_medico("dr_turnos1", "hematologia")
    for i in range(8):
        _crear_turno(client, token, _fecha_futura(i + 1))

    res = client.get("/turnos/recientes", headers=auth_headers(token))
    assert res.status_code == 200, res.text
    assert len(res.json()) == 5


def test_skip_permite_ver_mas_alla_del_decimo_turno(client, crear_medico):
    _, token = crear_medico("dr_turnos2", "hematologia")
    for i in range(15):
        _crear_turno(client, token, _fecha_futura(i + 1))

    # Antes del fix, ningun skip/limit exponia el turno 11+ porque el
    # backend cortaba en 10 sin importar lo que pidiera el cliente.
    res = client.get(
        "/turnos/recientes", params={"skip": 10, "limit": 5}, headers=auth_headers(token)
    )
    assert res.status_code == 200, res.text
    assert len(res.json()) == 5


def test_paginas_no_se_solapan(client, crear_medico):
    _, token = crear_medico("dr_turnos3", "hematologia")
    for i in range(10):
        _crear_turno(client, token, _fecha_futura(i + 1))

    pagina1 = client.get(
        "/turnos/recientes", params={"skip": 0, "limit": 5}, headers=auth_headers(token)
    ).json()
    pagina2 = client.get(
        "/turnos/recientes", params={"skip": 5, "limit": 5}, headers=auth_headers(token)
    ).json()

    ids_pagina1 = {t["id"] for t in pagina1}
    ids_pagina2 = {t["id"] for t in pagina2}
    assert ids_pagina1.isdisjoint(ids_pagina2)


def test_aislamiento_multitenant(client, crear_medico):
    _, token_a = crear_medico("dr_turnos4a", "hematologia")
    _, token_b = crear_medico("dr_turnos4b", "hematologia")

    for i in range(3):
        _crear_turno(client, token_a, _fecha_futura(i + 1))

    res = client.get("/turnos/recientes", headers=auth_headers(token_b))
    assert res.status_code == 200, res.text
    assert res.json() == []


def test_orden_ascendente_el_mas_proximo_primero(client, crear_medico):
    _, token = crear_medico("dr_turnos5", "hematologia")

    # Los creo fuera de orden a proposito: el orden en la respuesta tiene
    # que salir de ORDER BY fecha ASC, no del orden de insercion.
    lejano = _crear_turno(client, token, _fecha_futura(20))
    cercano = _crear_turno(client, token, _fecha_futura(1))
    medio = _crear_turno(client, token, _fecha_futura(5))

    res = client.get("/turnos/recientes", headers=auth_headers(token))
    assert res.status_code == 200, res.text
    ids = [t["id"] for t in res.json()]
    assert ids == [cercano["id"], medio["id"], lejano["id"]]


def test_turnos_pasados_no_aparecen(client, db_session, crear_medico):
    from app.models.turnos import Turno

    medico, token = crear_medico("dr_turnos6", "hematologia")

    turno_futuro = _crear_turno(client, token, _fecha_futura(2))

    # POST /turnos siempre valida contra el reloj actual del lado del
    # frontend, asi que un turno con fecha pasada se inserta directo por
    # la sesion de test.
    db_session.add(
        Turno(
            usuario_id=medico.id,
            nombre_temp="Paciente viejo",
            fecha=datetime.strptime(_fecha_pasada(3), "%Y-%m-%dT%H:%M:%S"),
            motivo="Control",
            estado="atendido",
        )
    )
    db_session.commit()

    res = client.get("/turnos/recientes", headers=auth_headers(token))
    assert res.status_code == 200, res.text
    ids = [t["id"] for t in res.json()]
    assert ids == [turno_futuro["id"]]

