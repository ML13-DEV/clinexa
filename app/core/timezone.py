from datetime import date, datetime
from zoneinfo import ZoneInfo

# Los datetime naive del proyecto (Turno.fecha, Nota.fecha, Analisis.fecha)
# representan la hora de Buenos Aires tal cual la tipeó el médico, no UTC
# (ver app/templates/paciente.html: crearTurno()/crearNota()). Cualquier
# cálculo de "hoy"/"ahora" del lado del servidor tiene que anclarse acá,
# no al reloj del servidor (Render corre en UTC por default) — si no, un
# turno cargado entre las 21:00 y las 23:59 ART queda comparado contra un
# "hoy" que el servidor ya considera el día siguiente.
ZONA_CONSULTORIO = ZoneInfo("America/Argentina/Buenos_Aires")


def hoy_consultorio() -> date:
    return datetime.now(ZONA_CONSULTORIO).date()
