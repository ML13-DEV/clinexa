"""Rate limiting en /login (ver app/core/limiter.py). CORS no se prueba
acá: CORSMiddleware queda configurado con la lista de origenes ya fija al
crear la app, así que no hay forma de parametrizarlo por test sin crear
una instancia de FastAPI nueva por caso; se verificó manualmente."""

from app.core.limiter import limiter


def test_login_bloquea_pasado_el_limite_de_intentos(client, crear_medico):
    crear_medico("drratelimit", "hematologia")

    limiter.reset()
    limiter.enabled = True
    try:
        credenciales = {"username": "drratelimit", "password": "incorrecta"}
        for _ in range(5):
            res = client.post("/login", json=credenciales)
            assert res.status_code == 401

        res = client.post("/login", json=credenciales)
        assert res.status_code == 429
    finally:
        limiter.enabled = False
