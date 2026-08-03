from slowapi import Limiter
from slowapi.util import get_remote_address

# Instancia compartida: se registra en app.state en main.py y se usa como
# decorador en las rutas que necesiten límite (hoy solo POST /login). Los
# tests la deshabilitan (ver tests/conftest.py) porque loguean muchas veces
# por corrida en pocos segundos.
limiter = Limiter(key_func=get_remote_address)
