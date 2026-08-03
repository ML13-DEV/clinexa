from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# override=True: que el .env del proyecto gane sobre variables de entorno
# que puedan estar seteadas a nivel de sistema (de otro proyecto, por ej.).
# Se hace acá, antes de instanciar Settings, porque pydantic-settings por
# default prioriza os.environ por sobre el propio env_file.
load_dotenv(override=True)


class Settings(BaseSettings):
    """Config tipada leída de variables de entorno (.env en local, env vars
    del Web Service en Render). SQLite es fallback de desarrollo: staging y
    producción siempre deben tener database_url seteada explícitamente."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    database_url: str = "sqlite:///./med.db"

    secret_key: str = "clave_de_emergencia"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Lista separada por comas de orígenes permitidos para CORS (ej.
    # "https://clinexa.onrender.com,https://clinexa.com.ar"). Vacío por
    # default: sin nada configurado, no se permite ningún origen cruzado
    # (el frontend server-rendered no lo necesita; los navegadores no
    # exigen CORS para requests same-origin).
    allowed_origins: str = ""

    # Límite de intentos de POST /login por IP, formato de la librería
    # `limits` (usada por slowapi). 5/minute: generoso para un error de
    # tipeo humano, restrictivo para fuerza bruta contra bcrypt.
    login_rate_limit: str = "5/minute"

    # Resend (resend.com) para el mail de reset de contraseña. Con el
    # dominio de pruebas (default de from) solo se puede mandar a la
    # dirección de la propia cuenta de Resend, hasta verificar un
    # dominio propio.
    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"

    # Base pública de la app (sin / final), para armar el link del mail
    # de reset. En Render, setear al dominio real del Web Service.
    app_base_url: str = "http://localhost:8000"

    reset_password_token_expire_minutes: int = 30

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
