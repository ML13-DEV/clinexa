from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.database import Base, engine
from app.routes import pacientes, turnos, notas, analisis, auth
from app.models.paciente import Paciente
from app.models.turnos import Turno
from app.models.nota import Nota
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(pacientes.router)
app.include_router(turnos.router)
app.include_router(notas.router)
app.include_router(analisis.router)
app.include_router(auth.router)

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
    
