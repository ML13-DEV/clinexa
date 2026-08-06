"""GET /turnos/recientes con skip/limit reales (antes tenia un .limit(10)
fijo en el backend, asi que nunca se podia ver mas alla del turno 10 sin
importar cuanto se clickeara "ver mas" en el frontend)."""

from tests.conftest import auth_headers


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
        _crear_turno(client, token, f"2026-08-{i + 1:02d}T10:00:00")

    res = client.get("/turnos/recientes", headers=auth_headers(token))
    assert res.status_code == 200, res.text
    assert len(res.json()) == 5


def test_skip_permite_ver_mas_alla_del_decimo_turno(client, crear_medico):
    _, token = crear_medico("dr_turnos2", "hematologia")
    for i in range(15):
        _crear_turno(client, token, f"2026-08-{i + 1:02d}T10:00:00")

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
        _crear_turno(client, token, f"2026-08-{i + 1:02d}T10:00:00")

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
        _crear_turno(client, token_a, f"2026-08-{i + 1:02d}T10:00:00")

    res = client.get("/turnos/recientes", headers=auth_headers(token_b))
    assert res.status_code == 200, res.text
    assert res.json() == []
