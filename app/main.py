from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.database import Base, engine
from app.routes import pacientes, turnos, notas, analisis, auth
from app.models.paciente import Paciente
from app.models.turnos import Turno
from app.models.nota import Nota
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.auth import hash_password
from app.models.usuario import Usuario # Asegúrate de que la ruta a tu modelo sea correcta

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
    


@app.get("/crear-usuario-inicial")
def crear_usuario_inicial(db: Session = Depends(get_db)):
    # Verificamos si ya existe el admin para no duplicarlo
    existe = db.query(Usuario).filter(Usuario.username == "admin").first()
    if existe:
        return {"msg": "El usuario admin ya existe"}
    
    nuevo_user = Usuario(
        username="admin",
        password=hash_password("1234") # Después la puedes cambiar
    )
    db.add(nuevo_user)
    db.commit()
    return {"msg": "Usuario admin creado exitosamente en la nube"}

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/agenda", response_class=HTMLResponse)
def ver_agenda(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="agenda.html"
    )
    
