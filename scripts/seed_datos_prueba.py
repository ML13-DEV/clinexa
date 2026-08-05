"""Genera pacientes/turnos/analisis de prueba para los medicos ya
existentes en la base (rol=medico), usando las funciones reales del
catalogo (validar_datos_clinicos, validar_analisis, calcular_imc,
recalcular_computados) para que el JSONB/analisis_valores generado
matchee siempre el catalogo vigente, no una copia a mano que puede
desincronizarse.

Idempotente por borrado: antes de generar, borra pacientes/turnos/notas/
analisis de los medicos encontrados (no toca usuarios ni datos de otros
roles) y arranca de cero. Pensado para un ambiente de pruebas, no
requiere confirmacion interactiva.

Uso:
    python scripts/seed_datos_prueba.py
Respeta el DATABASE_URL activo en el entorno donde se corre (mismo
criterio que las migraciones .sql: portable a donde apunte la sesion).
"""

import random
from datetime import date, datetime, timedelta

from app.core.timezone import ZONA_CONSULTORIO, hoy_consultorio
from app.database import SessionLocal
from app.especialidades.analisis_config import (
    TipoAnalisis,
    analisis_de,
    campos_computados,
    recalcular_computados,
    validar_analisis,
)
from app.especialidades.config import CAMPOS_POR_ESPECIALIDAD, TipoCampo, campos_de, validar_datos_clinicos
from app.models.analisis import Analisis, AnalisisValor
from app.models.nota import Nota
from app.models.paciente import Paciente
from app.models.rango_normal import RangoNormal
from app.models.turnos import Turno
from app.models.usuario import Usuario

random.seed(42)

FECHA_FIN_TURNOS = date(2026, 8, 31)
DIAS_TURNOS_PASADOS = 7
PACIENTES_POR_MEDICO = 50

NOMBRES = [
    "Juan", "Carlos", "Jorge", "Luis", "Miguel", "Diego", "Martin", "Pablo", "Sergio", "Ricardo",
    "Fernando", "Gabriel", "Nicolas", "Federico", "Ezequiel", "Matias", "Alejandro", "Gustavo", "Ramiro", "Ivan",
    "Maria", "Ana", "Laura", "Claudia", "Patricia", "Silvia", "Monica", "Andrea", "Valeria", "Carolina",
    "Sofia", "Lucia", "Florencia", "Julieta", "Camila", "Rosa", "Marta", "Susana", "Gladys", "Norma",
]

APELLIDOS = [
    "Gonzalez", "Rodriguez", "Fernandez", "Lopez", "Martinez", "Perez", "Garcia", "Sanchez", "Romero", "Sosa",
    "Torres", "Ruiz", "Flores", "Acosta", "Benitez", "Medina", "Herrera", "Aguirre", "Rios", "Molina",
    "Ortiz", "Suarez", "Ibañez", "Nuñez", "Vega", "Castro", "Rojas", "Silva", "Godoy", "Coronel",
]

LOCALIDADES = ["Rosario", "Venado Tuerto", "Santa Fe", "Rufino", "Casilda",
               "Firmat", "Cañada de Gomez", "Reconquista", "Rafaela", "Villa Constitucion"]
PESOS_LOCALIDADES = [30, 22, 18, 6, 6, 5, 5, 3, 3, 2]

DIAGNOSTICOS_POR_ESPECIALIDAD = {
    "hematologia": {
        "opciones": ["Anemia ferropenica", "Trombocitopenia", "Anemia megaloblastica",
                     "Policitemia vera", "Trombofilia", "Leucopenia", "Anemia hemolitica"],
        "pesos": [30, 22, 14, 12, 10, 7, 5],
    },
    "nutricion": {
        "opciones": ["Obesidad", "Sobrepeso", "Diabetes tipo 2", "Sindrome metabolico",
                     "Dislipemia", "Desnutricion", "Obesidad morbida"],
        "pesos": [28, 22, 18, 12, 10, 6, 4],
    },
    "cardiologia": {
        "opciones": ["Hipertension arterial", "Dislipemia", "Arritmia",
                     "Insuficiencia cardiaca", "Cardiopatia isquemica", "Fibrilacion auricular"],
        "pesos": [35, 20, 16, 12, 10, 7],
    },
    "neurologia": {
        "opciones": ["Migraña", "Epilepsia", "Cefalea tensional",
                     "Neuropatia periferica", "Enfermedad de Parkinson", "Esclerosis multiple"],
        "pesos": [32, 20, 18, 14, 9, 7],
    },
}

OBRAS_SOCIALES = ["OSDE", "Swiss Medical", "IAPOS", "PAMI", "Galeno", "Medife", "Particular", "Union Personal"]

MOTIVOS_TURNO = ["Control", "Primera consulta", "Seguimiento", "Consulta por sintomas",
                  "Revision de estudios", "Renovacion de receta"]

HORARIOS = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"]

FRASES_CLINICAS = {
    "sangrados": ["Sin sangrados activos", "Refiere gingivorragia ocasional", "Epistaxis frecuente", "Sin antecedentes de sangrado"],
    "trombosis": ["Sin antecedentes de trombosis", "TVP en miembro inferior hace 2 años", "Sin eventos tromboticos"],
    "vacunas": ["Esquema completo", "Falta refuerzo antigripal", "Esquema al dia"],
    "fim_descriptivo": ["Sin hallazgos relevantes", "Palidez cutaneo-mucosa leve", "Adenopatias cervicales pequeñas"],
    "alergias_alimentarias": ["Sin alergias conocidas", "Alergia a mariscos", "Intolerancia a la lactosa"],
    "plan_alimentario": ["Plan hipocalorico en curso", "Plan normocalorico fraccionado", "En evaluacion inicial"],
    "suplementacion": ["Sin suplementacion", "Vitamina D 2000 UI/dia", "Complejo B mensual"],
    "antecedentes_gastrointestinales": ["Sin antecedentes", "RGE ocasional", "Colon irritable"],
    "factores_riesgo_cv": ["Tabaquismo activo", "Sedentarismo", "Sin factores de riesgo", "Obesidad y sedentarismo"],
    "antecedentes_cardiovasculares": ["Sin antecedentes", "IAM hace 5 años", "Padres con cardiopatia isquemica"],
    "ecg_basal": ["Ritmo sinusal normal", "Bloqueo de rama derecha", "Sin alteraciones significativas"],
    "tratamiento_cardiologico": ["Enalapril 10mg/dia", "Atorvastatina 20mg/dia", "Sin tratamiento actual"],
    "antecedentes_neurologicos": ["Sin antecedentes", "Madre con migraña", "TEC leve hace 3 años"],
    "escala_funcional": ["Rankin 0", "Rankin 1", "Rankin 2"],
    "medicacion_neurologica": ["Sin medicacion", "Topiramato 50mg/dia", "Levetiracetam 500mg c/12hs"],
    "estudios_imagen": ["RMN sin hallazgos", "TAC de cerebro normal", "Pendiente de realizar"],
}

FRASES_ANALISIS_TEXTO = {
    "hepatograma": ["Dentro de parametros normales", "Transaminasas levemente elevadas"],
    "funcion_renal": ["Creatinina y urea normales", "Filtrado glomerular conservado"],
    "otros_analisis": ["Sin determinaciones adicionales", "Pendiente serologia"],
    "ecg_hallazgos": ["Ritmo sinusal", "Extrasistoles ventriculares aisladas"],
    "hallazgos_imagen": ["Sin hallazgos patologicos", "Leve atrofia cortical"],
    "observaciones": ["Buena evolucion", "Sin cambios respecto al control anterior", "A seguir control"],
}

# Bandas plausibles para determinaciones NUMERO que no tienen un
# RangoNormal cargado en la base (ver rangos_normales): no hay contra
# que colorear, asi que solo importa que el numero se vea razonable.
BANDAS_FALLBACK = {
    ("nutricion", "peso"): (55, 110),
    ("nutricion", "circunferencia_cintura"): (70, 115),
    ("nutricion", "circunferencia_cadera"): (85, 120),
    ("nutricion", "porcentaje_grasa_corporal"): (15, 40),
    ("nutricion", "porcentaje_masa_muscular"): (25, 45),
    ("cardiologia", "peso"): (55, 110),
    ("cardiologia", "troponina"): (0.01, 0.5),
    ("cardiologia", "bnp"): (10, 100),
    ("cardiologia", "saturacion_oxigeno"): (92, 99),
    ("neurologia", "escala_dolor"): (0, 10),
    ("neurologia", "frecuencia_episodios"): (0, 12),
    ("neurologia", "puntaje_cognitivo"): (18, 30),
}


def _variar_texto(valor: str) -> str:
    """Une puñado de casing/espacios distinto para poder confirmar en el
    browser que la normalizacion (TRIM+LOWER) de las estadisticas
    realmente agrupa estas variantes junto con el resto."""
    variante = random.choice(["normal", "mayus", "espacios"])
    if variante == "mayus":
        return valor.upper() if random.random() < 0.5 else valor.lower()
    if variante == "espacios":
        return f"  {valor}  "
    return valor


def generar_dni(usados: set[str]) -> str:
    while True:
        dni = str(random.randint(20_000_000, 46_000_000))
        if dni not in usados:
            usados.add(dni)
            return dni


def generar_fecha_nacimiento(hoy: date) -> date:
    bucket = random.choices(
        ["0-17", "18-30", "31-45", "46-60", "61+"],
        weights=[8, 22, 28, 24, 18],
    )[0]
    rangos = {"0-17": (1, 17), "18-30": (18, 30), "31-45": (31, 45), "46-60": (46, 60), "61+": (61, 90)}
    edad_min, edad_max = rangos[bucket]
    edad = random.randint(edad_min, edad_max)
    dias_extra = random.randint(0, 364)
    return date(hoy.year - edad, hoy.month, min(hoy.day, 28)) - timedelta(days=dias_extra)


def generar_peso_talla(fecha_nacimiento: date, hoy: date) -> tuple[float, float]:
    edad = hoy.year - fecha_nacimiento.year
    if edad < 18:
        talla = round(70 + edad * 6 + random.uniform(-3, 3), 1)
        peso = round(9 + edad * 2.5 + random.uniform(-2, 2), 1)
        return max(peso, 3), max(talla, 50)

    talla = round(random.uniform(150, 190), 1)
    imc_objetivo = random.uniform(19, 34)
    peso = round(imc_objetivo * (talla / 100) ** 2, 1)
    return peso, talla


def generar_datos_clinicos(especialidad: str) -> dict:
    datos = {}
    for campo in campos_de(especialidad):
        if random.random() < 0.1:
            continue
        if campo.tipo == TipoCampo.SELECT:
            datos[campo.key] = random.choice(campo.opciones)
        elif campo.tipo == TipoCampo.NUMERO:
            datos[campo.key] = round(random.uniform(60, 90), 1)
        elif campo.tipo == TipoCampo.TEXTO:
            datos[campo.key] = random.choice(FRASES_CLINICAS.get(campo.key, ["Sin datos adicionales"]))
        else:
            datos[campo.key] = random.choice(FRASES_CLINICAS.get(campo.key, ["Sin observaciones"]))
    return datos


def _valor_dentro_o_fuera(valor_min, valor_max, dentro: bool) -> float:
    if valor_min is not None and valor_max is not None:
        ancho = valor_max - valor_min
    elif valor_min is not None:
        ancho = valor_min * 0.5
    else:
        ancho = valor_max * 0.5
    ancho = ancho or 1.0

    if dentro:
        if valor_min is not None and valor_max is not None:
            return round(random.uniform(valor_min, valor_max), 2)
        if valor_min is not None:
            return round(random.uniform(valor_min * 1.05, valor_min * 2), 2)
        return round(random.uniform(max(valor_max * 0.3, 0.01), valor_max * 0.95), 2)

    hacia_abajo = valor_min is not None and (valor_max is None or random.random() < 0.5)
    if hacia_abajo:
        return round(max(valor_min - random.uniform(ancho * 0.15, ancho * 0.6), 0.01), 2)
    return round(valor_max + random.uniform(ancho * 0.15, ancho * 0.6), 2)


def generar_valores_analisis(especialidad: str, rangos: dict, peso_previo: float | None = None) -> dict:
    valores = {}
    for campo in analisis_de(especialidad):
        if campo.computado:
            continue
        if campo.tipo == TipoAnalisis.TEXTO:
            valores[campo.key] = random.choice(FRASES_ANALISIS_TEXTO.get(campo.key, ["Sin datos"]))
            continue

        if especialidad == "nutricion" and campo.key == "peso" and peso_previo is not None:
            valores[campo.key] = round(max(peso_previo + random.uniform(-1.5, 1.0), 30), 1)
            continue

        rango = rangos.get((especialidad, campo.key))
        if rango is not None:
            valor_min, valor_max = rango
            dentro = random.random() < 0.65
            valores[campo.key] = _valor_dentro_o_fuera(valor_min, valor_max, dentro)
        else:
            bajo, alto = BANDAS_FALLBACK.get((especialidad, campo.key), (1, 100))
            valores[campo.key] = round(random.uniform(bajo, alto), 2)

    valores.update(recalcular_computados(especialidad, valores))
    return valores


def limpiar_datos_de_prueba(db, medico_ids: list[int]) -> None:
    paciente_ids = [pid for (pid,) in db.query(Paciente.id).filter(Paciente.usuario_id.in_(medico_ids)).all()]

    if paciente_ids:
        analisis_ids = [aid for (aid,) in db.query(Analisis.id).filter(Analisis.paciente_id.in_(paciente_ids)).all()]
        if analisis_ids:
            db.query(AnalisisValor).filter(AnalisisValor.analisis_id.in_(analisis_ids)).delete(synchronize_session=False)
            db.query(Analisis).filter(Analisis.id.in_(analisis_ids)).delete(synchronize_session=False)
        db.query(Nota).filter(Nota.paciente_id.in_(paciente_ids)).delete(synchronize_session=False)

    db.query(Turno).filter(Turno.usuario_id.in_(medico_ids)).delete(synchronize_session=False)
    db.query(Paciente).filter(Paciente.usuario_id.in_(medico_ids)).delete(synchronize_session=False)
    db.commit()


def generar_pacientes(db, medico: Usuario, hoy: date, dni_usados: set[str]) -> list[Paciente]:
    especialidad = medico.especialidad
    diagnosticos = DIAGNOSTICOS_POR_ESPECIALIDAD[especialidad]
    pacientes = []

    for i in range(PACIENTES_POR_MEDICO):
        fecha_nacimiento = generar_fecha_nacimiento(hoy)
        peso, talla = generar_peso_talla(fecha_nacimiento, hoy)
        localidad = random.choices(LOCALIDADES, weights=PESOS_LOCALIDADES)[0]
        diagnostico = random.choices(diagnosticos["opciones"], weights=diagnosticos["pesos"])[0]

        if random.random() < 0.12:
            localidad = _variar_texto(localidad)
        if random.random() < 0.12:
            diagnostico = _variar_texto(diagnostico)

        datos_clinicos = generar_datos_clinicos(especialidad)
        validar_datos_clinicos(especialidad, datos_clinicos)

        creado_hace_dias = random.randint(0, 180)
        paciente = Paciente(
            usuario_id=medico.id,
            nombre=random.choice(NOMBRES),
            apellido=random.choice(APELLIDOS),
            dni=generar_dni(dni_usados),
            fecha_nacimiento=fecha_nacimiento,
            telefono=f"341{random.randint(1000000, 9999999)}",
            localidad=localidad,
            obra_social=random.choice(OBRAS_SOCIALES),
            numero_afiliado=str(random.randint(100000, 999999)),
            diagnostico_principal=diagnostico,
            peso=peso,
            talla=talla,
            datos_clinicos=datos_clinicos,
            created_at=datetime.combine(hoy, datetime.min.time(), tzinfo=ZONA_CONSULTORIO) - timedelta(days=creado_hace_dias),
        )
        paciente.imc = round(peso / ((talla / 100) ** 2), 2)
        db.add(paciente)
        pacientes.append(paciente)

    db.flush()
    return pacientes


def generar_turnos(db, medico: Usuario, pacientes: list[Paciente], hoy: date) -> int:
    cantidad = 0
    dia = hoy - timedelta(days=DIAS_TURNOS_PASADOS)

    while dia <= FECHA_FIN_TURNOS:
        es_pasado = dia < hoy
        horarios_del_dia = random.sample(HORARIOS, k=random.randint(2, 4))

        for horario in horarios_del_dia:
            hh, mm = (int(x) for x in horario.split(":"))
            fecha = datetime(dia.year, dia.month, dia.day, hh, mm)

            usar_paciente = random.random() < 0.75
            paciente = random.choice(pacientes) if usar_paciente else None

            turno = Turno(
                usuario_id=medico.id,
                paciente_id=paciente.id if paciente else None,
                nombre_temp=None if paciente else f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} (sin ficha)",
                fecha=fecha,
                motivo=random.choice(MOTIVOS_TURNO),
                estado="atendido" if es_pasado else "pendiente",
                diagnostico=(paciente.diagnostico_principal if (es_pasado and paciente) else None),
                observaciones=(random.choice(FRASES_ANALISIS_TEXTO["observaciones"]) if es_pasado else None),
            )
            db.add(turno)
            cantidad += 1

        dia += timedelta(days=1)

    db.flush()
    return cantidad


def generar_analisis(db, medico: Usuario, pacientes: list[Paciente], rangos: dict, hoy: date) -> tuple[int, int]:
    especialidad = medico.especialidad
    total_analisis = 0
    total_valores = 0

    for paciente in pacientes:
        cantidad = random.randint(2, 4)
        peso_previo = paciente.peso if especialidad == "nutricion" else None

        fechas = sorted(
            hoy - timedelta(days=random.randint(15, 330))
            for _ in range(cantidad)
        )

        for fecha in fechas:
            valores = generar_valores_analisis(especialidad, rangos, peso_previo)
            if especialidad == "nutricion":
                peso_previo = valores.get("peso", peso_previo)

            a_validar = {k: v for k, v in valores.items() if k not in campos_computados(especialidad)}
            validar_analisis(especialidad, a_validar)

            analisis = Analisis(paciente_id=paciente.id, fecha=datetime.combine(fecha, datetime.min.time()))
            db.add(analisis)
            db.flush()

            for key, valor in valores.items():
                if valor is not None:
                    db.add(AnalisisValor(analisis_id=analisis.id, analisis_key=key, valor=str(valor)))
                    total_valores += 1

            total_analisis += 1

    db.flush()
    return total_analisis, total_valores


def main():
    hoy = hoy_consultorio()
    db = SessionLocal()
    try:
        medicos = db.query(Usuario).filter(Usuario.rol == "medico").order_by(Usuario.id).all()
        if not medicos:
            print("No se encontraron usuarios con rol=medico. Corre primero "
                  "migrations/2026_07_28_seed_usuarios_de_prueba.sql o crea medicos desde /owner.")
            return

        print(f"Medicos encontrados ({len(medicos)}):")
        for m in medicos:
            print(f"  - {m.username} ({m.especialidad})")

        medicos_validos = [m for m in medicos if m.especialidad in CAMPOS_POR_ESPECIALIDAD]
        for m in medicos:
            if m.especialidad not in CAMPOS_POR_ESPECIALIDAD:
                print(f"  {m.username}: especialidad {m.especialidad!r} sin catalogo, salteado")

        limpiar_datos_de_prueba(db, [m.id for m in medicos_validos])

        rangos = {
            (r.especialidad, r.analisis_key): (r.valor_min, r.valor_max)
            for r in db.query(RangoNormal).all()
        }
        dni_usados: set[str] = set()

        for medico in medicos_validos:
            pacientes = generar_pacientes(db, medico, hoy, dni_usados)
            cantidad_turnos = generar_turnos(db, medico, pacientes, hoy)
            cantidad_analisis, cantidad_valores = generar_analisis(db, medico, pacientes, rangos, hoy)
            print(
                f"  {medico.username}: {len(pacientes)} pacientes, "
                f"{cantidad_turnos} turnos, {cantidad_analisis} analisis "
                f"({cantidad_valores} valores)"
            )

        db.commit()
        print("Listo.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
