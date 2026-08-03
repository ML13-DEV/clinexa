"""Flujo de "olvidé mi contraseña" (ver app/core/mail.py, app/core/
security.py). El envío real vía Resend se mockea: los tests no deben
pegarle a la red ni depender de una RESEND_API_KEY real."""

from app.core.security import hash_password
from app.models.usuario import Usuario

PASSWORD_ORIGINAL = "test1234"


def _crear_usuario_con_email(db_session, username="drconemail", email="dr@example.com"):
    usuario = Usuario(
        username=username,
        password=hash_password(PASSWORD_ORIGINAL),
        rol="medico",
        especialidad="hematologia",
        email=email,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


def _capturar_link(monkeypatch):
    """Reemplaza enviar_mail_reset por un stub que guarda el link
    generado, en vez de pegarle a la API real de Resend."""
    llamadas = []
    monkeypatch.setattr(
        "app.routes.auth.enviar_mail_reset",
        lambda destinatario, nombre, link: llamadas.append(link),
    )
    return llamadas


def _token_de(link: str) -> str:
    return link.split("token=")[1]


def test_solicitar_reset_manda_mail_si_tiene_email(client, db_session, monkeypatch):
    _crear_usuario_con_email(db_session)
    llamadas = _capturar_link(monkeypatch)

    res = client.post("/olvide-password", json={"identificador": "drconemail"})
    assert res.status_code == 200
    assert len(llamadas) == 1


def test_solicitar_reset_no_manda_mail_si_no_tiene_email(client, crear_medico, monkeypatch):
    crear_medico("drsinemail", "hematologia")
    llamadas = _capturar_link(monkeypatch)

    res = client.post("/olvide-password", json={"identificador": "drsinemail"})
    assert res.status_code == 200
    assert len(llamadas) == 0


def test_solicitar_reset_usuario_inexistente_responde_igual(client, monkeypatch):
    """Mismo mensaje y mismo status exista o no la cuenta: no hay que dar
    ninguna señal de qué usuarios existen."""
    llamadas = _capturar_link(monkeypatch)

    res_inexistente = client.post("/olvide-password", json={"identificador": "no_existe"})
    res_existente = client.post("/olvide-password", json={"identificador": "tampoco"})

    assert res_inexistente.status_code == res_existente.status_code == 200
    assert res_inexistente.json() == res_existente.json()
    assert len(llamadas) == 0


def test_solicitar_reset_funciona_por_email_ademas_de_username(client, db_session, monkeypatch):
    _crear_usuario_con_email(db_session, username="drporemail", email="porsuemail@example.com")
    llamadas = _capturar_link(monkeypatch)

    res = client.post("/olvide-password", json={"identificador": "porsuemail@example.com"})
    assert res.status_code == 200
    assert len(llamadas) == 1


def test_flujo_completo_de_reset_cambia_la_contrasena(client, db_session, monkeypatch):
    _crear_usuario_con_email(db_session, username="drreset")
    llamadas = _capturar_link(monkeypatch)

    client.post("/olvide-password", json={"identificador": "drreset"})
    token = _token_de(llamadas[0])

    res = client.post("/reset-password", json={"token": token, "password_nueva": "nuevaClave123"})
    assert res.status_code == 200

    res_vieja = client.post("/login", json={"username": "drreset", "password": PASSWORD_ORIGINAL})
    assert res_vieja.status_code == 401

    res_nueva = client.post("/login", json={"username": "drreset", "password": "nuevaClave123"})
    assert res_nueva.status_code == 200


def test_token_de_reset_no_sirve_dos_veces(client, db_session, monkeypatch):
    """El token no tiene tabla propia de un solo uso: se invalida porque
    lleva un fingerprint del hash de contraseña vigente al emitirlo, que
    deja de matchear apenas la contraseña cambia una vez."""
    _crear_usuario_con_email(db_session, username="drreusa")
    llamadas = _capturar_link(monkeypatch)

    client.post("/olvide-password", json={"identificador": "drreusa"})
    token = _token_de(llamadas[0])

    res1 = client.post("/reset-password", json={"token": token, "password_nueva": "primeraClave1"})
    assert res1.status_code == 200

    res2 = client.post("/reset-password", json={"token": token, "password_nueva": "segundaClave2"})
    assert res2.status_code == 400


def test_reset_con_token_invalido_es_400(client):
    res = client.post("/reset-password", json={"token": "esto-no-es-un-token", "password_nueva": "loquesea1"})
    assert res.status_code == 400


def test_token_de_reset_no_sirve_como_sesion(client, db_session, monkeypatch):
    """Un link de reset interceptado no debe poder usarse como Bearer
    token para autenticarse (ver get_current_user)."""
    _crear_usuario_con_email(db_session, username="drtokenreset")
    llamadas = _capturar_link(monkeypatch)

    client.post("/olvide-password", json={"identificador": "drtokenreset"})
    token = _token_de(llamadas[0])

    res = client.get("/pacientes", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
