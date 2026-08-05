import os

import dotenv

# Tiene que pasar antes de cualquier import de `app.*`: app.core.config lee
# DATABASE_URL al importarse, y sin esto los tests quedarían a merced de lo
# que haya seteado en el sistema (ej. una DATABASE_URL de otro proyecto) o,
# peor, de un .env real con una DATABASE_URL de Supabase: config.py usa
# load_dotenv(override=True) a propósito para ganarle a una env var de
# sistema, pero eso mismo le ganaría a esta asignación si no neutralizamos
# load_dotenv acá — un os.environ seteado antes no alcanza.
dotenv.load_dotenv = lambda *args, **kwargs: False
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.core.limiter import limiter
from app.core.security import hash_password
from app.database import Base
from app.main import app
from app.models.usuario import Usuario

# Los fixtures de abajo loguean varias veces por test; con el rate limit de
# /login activo (5/minute en prod) la suite completa lo pisaría en segundos.
# Los tests que sí quieren probar el límite lo reactivan puntualmente
# (ver tests/test_seguridad.py) y lo dejan como estaba en el finally.
limiter.enabled = False

PASSWORD = "test1234"


@pytest.fixture()
def db_session():
    """Una base SQLite en memoria por test, aislada de la real (ver
    DATABASE_URL arriba). StaticPool para que todas las conexiones de este
    engine (la nuestra y la que use el TestClient) vean la misma DB en
    memoria en vez de una por conexión."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _crear_usuario_y_loguear(db_session, client, username, rol, especialidad):
    usuario = Usuario(
        username=username,
        password=hash_password(PASSWORD),
        rol=rol,
        especialidad=especialidad,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)

    res = client.post("/login", json={"username": username, "password": PASSWORD})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return usuario, token


@pytest.fixture()
def crear_medico(db_session, client):
    """Factory fixture: crear_medico("drhemato", "hematologia") -> (Usuario, token)."""
    def _crear(username, especialidad):
        return _crear_usuario_y_loguear(db_session, client, username, "medico", especialidad)
    return _crear


@pytest.fixture()
def crear_owner(db_session, client):
    def _crear(username="owner_test"):
        return _crear_usuario_y_loguear(db_session, client, username, "owner", "sistema")
    return _crear


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
