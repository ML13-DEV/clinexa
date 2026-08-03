from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.limiter import limiter
from app.database import Base, engine

# MODELOS
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.turnos import Turno
from app.models.nota import Nota
from app.models.analisis import Analisis, AnalisisValor
from app.models.rango_normal import RangoNormal

# ROUTES
from app.routes import pacientes, turnos, notas, auth, analisis, especialidades
from app.routes import owner

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS: sin ALLOWED_ORIGINS seteada, ningún origen cruzado queda permitido
# (el frontend Jinja2 es same-origin y no lo necesita). allow_credentials
# en False porque la auth es JWT en localStorage/header, no cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(pacientes.router)
app.include_router(turnos.router)
app.include_router(notas.router)
app.include_router(analisis.router)
app.include_router(auth.router)
app.include_router(owner.router)
app.include_router(especialidades.router)

templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/paciente/{id}", response_class=HTMLResponse)
def ver_paciente(request: Request, id: int):
    return templates.TemplateResponse(
        request=request,
        name="paciente.html",
        context={"id": id}
    )
    


app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/agenda", response_class=HTMLResponse)
def ver_agenda(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="agenda.html"
    )


@app.get("/estadisticas", response_class=HTMLResponse)
def ver_estadisticas(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="estadisticas.html"
    )

