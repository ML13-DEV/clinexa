from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

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

